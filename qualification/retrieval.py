"""CPU feasibility and honest abstention evaluation; not the final chatbot."""

import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import time

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".qualification"
FIXTURE = Path(__file__).with_name("retrieval-fixture.json")


def eligible(source):
    return source["state"] == "published" and source["kind"] in {"faq", "epic", "story", "spec"} and source["revision"] == source["current_revision"]


def main():
    started = time.perf_counter()
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    # The reference host hypothesis is two vCPUs, not all workstation cores.
    torch.set_num_threads(2)
    corpus = json.loads(FIXTURE.read_text())
    model = SentenceTransformer(str(WORK / "model"), device="cpu", local_files_only=True)
    load_seconds = time.perf_counter() - started
    sources = [source for source in corpus["sources"] if eligible(source)]
    started = time.perf_counter()
    vectors = model.encode([f"passage: {s['title']}\n{s['text']}" for s in sources], normalize_embeddings=True, batch_size=16, show_progress_bar=False)
    index_seconds = time.perf_counter()-started
    latencies = []

    def score_questions(questions):
        output = []
        for row in questions:
            start = time.perf_counter()
            vector = model.encode(["query: " + row["question"]], normalize_embeddings=True, show_progress_bar=False)[0]
            scores = vectors @ vector
            order = np.argsort(-scores)
            latencies.append((time.perf_counter()-start)*1000)
            output.append({**row, "top": sources[order[0]]["id"], "score": float(scores[order[0]]), "margin": float(scores[order[0]]-scores[order[1]])})
        return output

    calibration = score_questions(corpus["calibration"])

    def evaluate(rows, threshold, margin):
        correct = false_positive = misses = wrong = 0
        details = []
        for row in rows:
            decision = row["top"] if row["score"] >= threshold and row["margin"] >= margin else None
            expected = row["expected"]
            correct += expected is not None and decision == expected
            false_positive += expected is None and decision is not None
            misses += expected is not None and decision is None
            wrong += expected is not None and decision is not None and decision != expected
            details.append({**row, "returned": decision, "passed": decision == expected})
        return {"correct_destinations": correct, "answerable": sum(row["expected"] is not None for row in rows), "false_answers": false_positive,
                "unanswerable": sum(row["expected"] is None for row in rows), "abstained_answerable": misses, "wrong_destinations": wrong, "cases": details}

    # Select from a declared grid using calibration only. Prioritize zero false answers.
    candidates = []
    for threshold in np.arange(.70, .961, .005):
        for margin in np.arange(0, .101, .005):
            stats = evaluate(calibration, float(threshold), float(margin))
            objective = (-stats["false_answers"], -stats["wrong_destinations"], stats["correct_destinations"], float(threshold), float(margin))
            candidates.append((objective, float(threshold), float(margin)))
    _, threshold, margin = max(candidates)
    policy = {"minimum_cosine": round(threshold, 6), "minimum_top_two_margin": round(margin, 6), "returns_maximum": 1,
              "calibration_fixture_sha256": hashlib.sha256(json.dumps(corpus["calibration"], sort_keys=True).encode()).hexdigest(),
              "note": "Semantic-only feasibility baseline. Scores are not probabilities; no lexical search or contradiction classifier is implemented here."}
    (WORK / "retrieval-policy.json").write_text(json.dumps(policy, indent=2)+"\n")
    # The held-out questions are first scored after the chosen policy has been saved.
    held_out = score_questions(corpus["held_out"])
    evaluation = evaluate(held_out, threshold, margin)
    assert len(sources) == 20 and not any(s["id"] in {"private-draft", "archive-only", "file", "stale"} for s in sources)
    # Re-check the final gate after a hypothetical publication/archive between ranking and return.
    changed = dict(sources[0], current_revision=2)
    final_gate = not eligible(changed) and not eligible(dict(sources[0], state="archived"))
    # Measure ranking cost separately at the specification's initial 10,000-passage envelope.
    large = np.tile(vectors, (500, 1))
    sample = vectors[0]
    ranking_times = []
    for _ in range(30):
        start = time.perf_counter()
        np.argsort(-(large @ sample))[:3]
        ranking_times.append((time.perf_counter()-start)*1000)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() != "Darwin":
        rss *= 1024
    report = {"platform": platform.platform(), "python": platform.python_version(), "device": "cpu", "torch_threads": 2,
              "model_load_seconds_including_imports": load_seconds, "index_seconds": index_seconds, "indexed_passages": len(sources),
              "dimensions": int(vectors.shape[1]), "max_tokens": model.max_seq_length, "model_directory_bytes": sum(p.stat().st_size for p in (WORK / "model").rglob("*") if p.is_file()),
              "query_p50_ms": float(np.percentile(latencies, 50)), "query_p95_ms": float(np.percentile(latencies, 95)), "peak_rss_mib": rss/(1024*1024),
              "ranking_10000_p95_ms": float(np.percentile(ranking_times, 95)), "vectors_10000_mib": large.nbytes/(1024*1024),
              "policy": policy, "calibration": evaluate(calibration, threshold, margin), "held_out": evaluation,
              "source_gate": {"ineligible_excluded": 4, "post_ranking_recheck_passed": final_gate},
              "acceptance_target_met": evaluation["correct_destinations"]/evaluation["answerable"] >= .9 and evaluation["false_answers"] == 0 and evaluation["wrong_destinations"] == 0 and final_gate}
    (WORK / "retrieval-results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({key: value for key, value in report.items() if key not in {"calibration", "held_out"}}, indent=2))
    for name in ["calibration", "held_out"]:
        print(name, {key: value for key, value in report[name].items() if key != "cases"})


if __name__ == "__main__":
    main()
