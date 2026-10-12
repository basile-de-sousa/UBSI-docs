"""Experimental hybrid policy. Activation requires separate reviewed evidence."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from django.conf import settings

ENCODER_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
RERANKER_REVISION = "1427fd652930e4ba29e8149678df786c240d8825"
INDEX_VERSION = "m6.1:" + ENCODER_REVISION
POLICY = {
    "version": "hybrid-m6.1-experimental",
    "semantic_candidates": 16, "lexical_candidates": 16,
    "minimum_cosine": .80, "minimum_rerank": 2.0, "minimum_margin": 3.0,
    "chunk_tokens": 350, "overlap_tokens": 50, "maximum_sources": 1,
    "encoder": ENCODER_REVISION, "reranker": RERANKER_REVISION,
}
FALLBACK = "Aucune réponse adaptée n’a été trouvée. Allez en parler aux urbanistes."
UNAVAILABLE = "La recherche de réponses est temporairement indisponible. Réessayez dans quelques instants."
PENDING = "L’assistant est en cours de qualification. Vous pouvez consulter la FAQ et utiliser la recherche."


class Unavailable(Exception):
    pass


class Busy(Unavailable):
    pass


class InvalidQuestion(ValueError):
    pass


def normalize(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(re.findall(r"\w+", "".join(c for c in value if not unicodedata.combining(c))))


def fingerprint():
    # Editing decision/index/runtime code invalidates a previous activation report.
    digest = hashlib.sha256(json.dumps(POLICY, sort_keys=True).encode())
    for name in ["policy.py", "retrieval.py", "runtime.py", "corpus.py", "semantic.py"]:
        digest.update(Path(__file__).with_name(name).read_bytes())
    digest.update(Path(__file__).with_name("assets.lock.json").read_bytes())
    return digest.hexdigest()


def warm_if_qualified():
    if qualification():
        from .runtime import Inference
        try:
            with Inference():
                pass
        except Unavailable:
            # The site's knowledge pages remain usable; readiness will fail
            # until the qualified model is available after process restart.
            pass


def qualification():
    """An operator-maintained private report; the web UI cannot approve itself."""
    if not settings.CHATBOT_QUALIFICATION_FILE:
        return False
    try:
        path = settings.CHATBOT_QUALIFICATION_FILE
        if path.stat().st_size > 512 * 1024:
            return False
        report = json.loads(path.read_text())
        if report["policy_sha256"] != fingerprint() or report["review"]["role"] != "urbanist" or report["review"]["expectations_approved"] is not True:
            return False
        if not report["review"]["date"] or report["policy_frozen_before_holdout"] is not True:
            return False
        groups = report["groups"]
        if len(groups["calibration"]) < 30 or len(groups["held_out"]) < 30 or len(groups["m0_regressions"]) < 60:
            return False
        ids = [r["id"] for rows in groups.values() for r in rows]
        if len(ids) != len(set(ids)):
            return False
        for group in ("held_out", "m0_regressions"):
            rows = groups[group]
            answerable = [r for r in rows if r["expected"]]
            if not answerable or sum(bool(set(r["expected"]) & set(r["returned"])) for r in answerable) / len(answerable) < .9:
                return False
            for row in rows:
                if row["status"] not in {"answer", "no_answer"} or row["private_or_stale"] is not False:
                    return False
                if set(row["returned"]) - set(row["expected"]):
                    return False
                if bool(row["returned"]) != (row["status"] == "answer"):
                    return False
        return report["lifecycle_checks_passed"] is True
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False
