"""Second, local retrieval experiment; V1 holdout remains regression evidence.

The new evaluation questions are stored before running this experiment. No
threshold is tuned on either old or new held-out questions.
"""

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

from retrieval import eligible

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".qualification"
HERE = Path(__file__).parent


def main():
    started = time.perf_counter()
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer, CrossEncoder
    torch.set_num_threads(2)
    corpus = json.loads((HERE / "retrieval-fixture.json").read_text())
    sources = [s for s in corpus["sources"] if eligible(s)]
    model = SentenceTransformer(str(WORK / "model"), device="cpu", local_files_only=True)
    reranker = CrossEncoder(str(WORK / "reranker"), device="cpu", local_files_only=True)
    load_seconds = time.perf_counter()-started
    passages = [f"{s['title']}\n{s['text']}" for s in sources]
    vectors = model.encode(["passage: " + text for text in passages], normalize_embeddings=True, show_progress_bar=False)
    latencies = []

    def score(rows):
        output = []
        for row in rows:
            start = time.perf_counter()
            query = model.encode(["query: " + row["question"]], normalize_embeddings=True, show_progress_bar=False)[0]
            indices = np.argsort(-(vectors @ query))[:8]
            values = np.asarray(reranker.predict([(row["question"], passages[i]) for i in indices], batch_size=8, show_progress_bar=False)).reshape(-1)
            order = np.argsort(-values)
            latencies.append((time.perf_counter()-start)*1000)
            output.append({**row, "top": sources[indices[order[0]]]["id"], "score": float(values[order[0]]), "margin": float(values[order[0]]-values[order[1]])})
        return output

    def evaluate(rows, threshold, margin):
        cases = [{**r, "returned": r["top"] if r["score"] >= threshold and r["margin"] >= margin else None} for r in rows]
        for row in cases:
            row["passed"] = row["returned"] == row["expected"]
        return {"correct_destinations": sum(r["expected"] is not None and r["passed"] for r in cases),
                "answerable": sum(r["expected"] is not None for r in cases),
                "false_answers": sum(r["expected"] is None and r["returned"] is not None for r in cases),
                "unanswerable": sum(r["expected"] is None for r in cases),
                "wrong_destinations": sum(r["expected"] is not None and r["returned"] is not None and not r["passed"] for r in cases), "cases": cases}

    calibration = score(corpus["calibration"])
    # Scores are model-specific, not calibrated probabilities; candidates span observed calibration values.
    thresholds = sorted({-100., *[r["score"] for r in calibration], *[r["score"]+1e-6 for r in calibration]})
    margins = sorted({0., *[r["margin"] for r in calibration], *[r["margin"]+1e-6 for r in calibration]})
    candidates = []
    for threshold in thresholds:
        for margin in margins:
            result = evaluate(calibration, threshold, margin)
            candidates.append(((-result["false_answers"], -result["wrong_destinations"], result["correct_destinations"], threshold, margin), threshold, margin))
    _, threshold, margin = max(candidates)
    policy = {"candidate_count": 8, "minimum_score": threshold, "minimum_margin": margin, "returns_maximum": 1,
              "calibration_sha256": hashlib.sha256(json.dumps(corpus["calibration"], sort_keys=True).encode()).hexdigest(),
              "held_out_v2_sha256": hashlib.sha256((HERE / "retrieval-holdout-v2.json").read_bytes()).hexdigest()}
    (WORK / "rerank-policy.json").write_text(json.dumps(policy, indent=2)+"\n")
    held_out = score(json.loads((HERE / "retrieval-holdout-v2.json").read_text()))
    regression = score(corpus["held_out"])
    evaluation = evaluate(held_out, threshold, margin)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() != "Darwin":
        rss *= 1024
    report = {"experiment": "E5 top-8 + multilingual local cross-encoder", "cpu_threads": 2,
              "load_seconds_including_imports": load_seconds, "peak_rss_mib": rss/1024**2,
              "query_p50_ms": float(np.percentile(latencies, 50)), "query_p95_ms": float(np.percentile(latencies, 95)),
              "model_directories_bytes": sum(p.stat().st_size for name in ["model", "reranker"] for p in (WORK/name).rglob("*") if p.is_file()),
              "policy": policy, "calibration": evaluate(calibration, threshold, margin), "held_out_v2": evaluation,
              "v1_holdout_regression": evaluate(regression, threshold, margin),
              "acceptance_target_met": evaluation["correct_destinations"]/evaluation["answerable"] >= .9 and evaluation["false_answers"] == 0 and evaluation["wrong_destinations"] == 0}
    (WORK / "rerank-results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in {"calibration", "held_out_v2", "v1_holdout_regression"}}, indent=2))
    for split in ["calibration", "held_out_v2", "v1_holdout_regression"]:
        print(split, {k:v for k,v in report[split].items() if k != "cases"})


if __name__ == "__main__":
    main()
