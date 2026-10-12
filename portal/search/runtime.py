"""One offline CPU model pair per process; bounded inputs, no generated answers."""
import hashlib
import json
import os
from pathlib import Path
import threading

from django.conf import settings
from .policy import Busy, InvalidQuestion, POLICY, Unavailable

_lock = threading.Lock()
_models = None


def verify_assets(root):
    lock = json.loads(Path(__file__).with_name("assets.lock.json").read_text())
    for item in lock["files"]:
        path = root / item["path"]
        if not path.is_file() or path.is_symlink():
            raise Unavailable
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != item["sha256"]:
                raise Unavailable


def models():
    global _models
    if _models is None:
        try:
            root = settings.SEARCH_MODEL_ROOT
            verify_assets(root)
            os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false", HF_HUB_DISABLE_TELEMETRY="1", HF_HUB_DISABLE_PROGRESS_BARS="1")
            import torch
            from sentence_transformers import CrossEncoder, SentenceTransformer
            torch.set_num_threads(settings.SEARCH_CPU_THREADS)
            encoder = SentenceTransformer(str(root / "model"), device="cpu", local_files_only=True, trust_remote_code=False)
            reranker = CrossEncoder(str(root / "reranker"), device="cpu", local_files_only=True, trust_remote_code=False, max_length=512)
            if encoder.get_embedding_dimension() != 384 or encoder.max_seq_length != 512:
                raise Unavailable
            _models = encoder, reranker
        except Exception:
            raise Unavailable from None
    return _models


class Inference:
    def __enter__(self):
        if not _lock.acquire(timeout=settings.SEARCH_INFERENCE_WAIT_SECONDS):
            raise Busy
        try:
            self.encoder, self.reranker = models()
        except BaseException:
            _lock.release()
            raise
        return self

    def __exit__(self, *args):
        _lock.release()

    def query(self, question):
        if len(self.encoder.tokenizer.encode("query: " + question)) > 512:
            raise InvalidQuestion("La question dépasse la capacité du moteur. Raccourcissez-la.")
        return self.encoder.encode(["query: " + question], normalize_embeddings=True, show_progress_bar=False)[0]

    def chunk(self, title, text):
        tokenizer = self.encoder.tokenizer
        offsets = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
        budget = min(POLICY["chunk_tokens"], 512 - len(tokenizer.encode("passage: " + title + "\n")) - 4)
        if budget <= POLICY["overlap_tokens"]:
            raise Unavailable
        output = []
        start = 0
        while start < len(offsets):
            stop = min(start + budget, len(offsets))
            left, right = offsets[start][0], offsets[stop-1][1]
            # Zero-width special offsets cannot become source excerpts.
            if right > left:
                content = "passage: " + title + "\n" + text[left:right]
                if len(tokenizer.encode(content)) > 512:
                    raise Unavailable
                output.append((left, right, content))
            if stop == len(offsets): break
            start = stop - POLICY["overlap_tokens"]
        return output

    def encode(self, texts):
        return self.encoder.encode(texts, normalize_embeddings=True, batch_size=16, show_progress_bar=False)

    def rerank(self, question, texts):
        # Inputs, including aliases/headings, are data. No prompt execution exists.
        tokenizer = self.reranker.tokenizer
        if any(len(tokenizer.encode(question, text)) > 512 for text in texts):
            raise Unavailable
        return self.reranker.predict([(question, text) for text in texts], batch_size=8, show_progress_bar=False)


def loaded():
    return _models is not None
