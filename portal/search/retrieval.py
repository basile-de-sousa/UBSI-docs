"""Hybrid candidate selection with explicit abstention and a final source gate.

This is a candidate policy, not accepted business behavior. Only reviewed
qualification evidence can activate it for readers.
"""
from collections import defaultdict
from datetime import timedelta
import math
import re
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core import signing
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from knowledge.models import ProjectState
from .corpus import passages, records, source_digest, validate_passage
from .models import RetrievalSlot, SemanticChunk, SemanticIndex
from .policy import Busy, FALLBACK, INDEX_VERSION, InvalidQuestion, POLICY, Unavailable, normalize
from .runtime import Inference


def generation():
    return ProjectState.objects.values_list("search_generation", flat=True).get(pk=1)


def snapshot():
    before = generation()
    rows = list(passages().select_related("record", "revision").order_by("revision_id", "ordinal"))
    groups = defaultdict(list)
    for row in rows: groups[row.revision_id].append(row)
    # Missing lexical data or semantic preparation never means 'no answer'.
    expected = set(records().values_list("current_revision_id", flat=True))
    if expected != set(groups): raise Unavailable
    indexes = {index.revision_id: index for index in SemanticIndex.objects.filter(revision_id__in=expected)}
    for revision, group in groups.items():
        index = indexes.get(revision)
        if not index or index.version != INDEX_VERSION or index.source_digest != source_digest(group):
            raise Unavailable
    chunks = list(SemanticChunk.objects.filter(passage_id__in=[row.pk for row in rows]).order_by("passage_id", "ordinal"))
    if set(chunk.passage_id for chunk in chunks) != set(row.pk for row in rows) or len(chunks) > settings.SEARCH_MAX_CHUNKS or sum(index.chunk_count for index in indexes.values()) != len(chunks):
        raise Unavailable
    if generation() != before: raise Unavailable
    return before, {row.pk: row for row in rows}, chunks


@transaction.atomic
def acquire_slot():
    now = timezone.now()
    slot = RetrievalSlot.objects.select_for_update(skip_locked=True).filter(Q(lease_until__isnull=True) | Q(lease_until__lt=now)).order_by("id").first()
    if not slot: raise Busy
    slot.token, slot.lease_until = uuid4(), now + timedelta(seconds=35)
    slot.save()
    return slot.pk, slot.token


def answer(question):
    slot, token = acquire_slot()
    try:
        return rank(question)
    finally:
        RetrievalSlot.objects.filter(pk=slot, token=token).update(token=None, lease_until=None)


def rank(question):
    import numpy as np
    before, sources, chunks = snapshot()
    if not sources: return final(before, [])
    with Inference() as engine:
        vector = engine.query(question)
        matrix = np.stack([np.frombuffer(bytes(chunk.embedding), dtype="<f4") for chunk in chunks])
        if matrix.shape != (len(chunks), 384) or not np.isfinite(matrix).all() or not np.allclose(np.linalg.norm(matrix, axis=1), 1, atol=.01):
            raise Unavailable
        similarities = matrix @ vector
        order = np.argsort(-similarities)[:POLICY["semantic_candidates"]]
        candidate_ids = {chunks[int(i)].passage_id for i in order}
        query = SearchQuery(question, config="french", search_type="websearch")
        lexical = list(passages().filter(vector=query).annotate(rank=SearchRank("vector", query)).order_by("-rank", "id").values_list("id", flat=True)[:POLICY["lexical_candidates"]])
        candidate_ids.update(lexical)
        exact = set()
        for row in sources.values():
            if row.record.kind == "faq" and normalize(question) in {normalize(row.revision.title), *map(normalize, row.revision.payload.get("aliases", []))}:
                exact.add(row.pk)
        candidate_ids.update(exact)
        if len(candidate_ids) > 64: raise Unavailable
        # One best bounded excerpt per section; include every candidate section.
        best = {}
        for i, chunk in enumerate(chunks):
            if chunk.passage_id not in candidate_ids: continue
            if chunk.passage_id not in best or similarities[i] > best[chunk.passage_id][0]:
                best[chunk.passage_id] = (float(similarities[i]), chunk)
        candidates = []
        for key, (cosine, chunk) in best.items():
            row = sources[key]
            if not 0 <= chunk.start < chunk.end <= len(row.excerpt): raise Unavailable
            excerpt = row.excerpt[chunk.start:chunk.end]
            tokenizer = engine.reranker.tokenizer
            header = row.revision.title + "\n"
            budget = 512 - len(tokenizer.encode(question, header)) - 4
            if budget < 32: raise InvalidQuestion
            offsets = tokenizer(excerpt, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
            end = chunk.end
            if len(offsets) > budget:
                end = chunk.start + offsets[budget-1][1]
                excerpt = row.excerpt[chunk.start:end]
            candidates.append({"passage": row, "cosine": cosine, "excerpt": excerpt, "start": chunk.start, "end": end})
        # Cross-encoder uses another tokenizer. Refuse truncation of question or evidence.
        scores = engine.rerank(question, [candidate["passage"].revision.title + "\n" + candidate["excerpt"] for candidate in candidates])
        for candidate, score in zip(candidates, scores, strict=True):
            candidate["score"] = float(score)
            if not math.isfinite(candidate["score"]): raise Unavailable
    candidates.sort(key=lambda c: (-c["score"], c["passage"].pk))
    if not candidates: raise Unavailable
    chosen = candidates[0]
    # Exact FAQ questions/aliases use their full answer for the duplicate-answer guard.
    if exact:
        matches = [c for c in candidates if c["passage"].pk in exact]
        if len({normalize(c["passage"].excerpt) for c in matches}) != 1:
            return final(before, [])
        chosen = matches[0]
    # Competing sections with the same question/title but different rules are
    # ambiguous even when their ranking scores are far apart (e.g. negation).
    label = normalize(chosen["passage"].revision.title)
    if any(normalize(row.revision.title) == label and normalize(row.excerpt) != normalize(chosen["passage"].excerpt) and row.record_id != chosen["passage"].record_id for row in sources.values()):
        return final(before, [])
    # Explicit reference codes/numbers in a question must occur in its evidence.
    identifiers = re.findall(r"\b[A-Za-z]+(?:[-_]\w+)+\b|\b\d+\b", question)
    evidence = normalize(chosen["passage"].revision.title + " " + chosen["excerpt"])
    if any(normalize(identifier) not in evidence for identifier in identifiers):
        return final(before, [])
    if not exact:
        competitors = [candidate for candidate in candidates if candidate["passage"].record_id != chosen["passage"].record_id or candidate["passage"].section != chosen["passage"].section]
        margin = chosen["score"] - competitors[0]["score"] if competitors else float("inf")
        if chosen["cosine"] < POLICY["minimum_cosine"] or chosen["score"] < POLICY["minimum_rerank"] or margin < POLICY["minimum_margin"]:
            return final(before, [])
    return final(before, [chosen])


@transaction.atomic
def final(before, candidates):
    state = ProjectState.objects.select_for_update().get(pk=1)
    if state.search_generation != before: raise Unavailable
    cards = []
    for candidate in candidates[:3]:
        old = candidate["passage"]
        row = passages().select_related("record", "revision").filter(pk=old.pk, revision_id=old.revision_id).first()
        if not row: raise Unavailable
        validate_passage(row)
        excerpt = candidate["excerpt"]
        if row.excerpt[candidate["start"]:candidate["end"]] != excerpt: raise Unavailable
        token = signing.dumps({"record": str(row.record_id), "revision": str(row.revision_id), "section": row.section}, salt="search.source", compress=True)
        cards.append({"title": row.revision.title, "reference": row.record.reference, "section": row.title, "excerpt": excerpt[:600], "excerpt_truncated": len(excerpt) > 600, "url": reverse("search-source", args=[token])})
    return {"status": "answer" if cards else "no_answer", "message": "Voici une source publiée qui peut répondre à votre question." if cards else FALLBACK, "sources": cards}
