import threading
from typing import List

import numpy as np

from .config import EMBEDDING_MODEL, RAG_MODEL_CACHE

_model = None
_lock = threading.Lock()

# bge models expect this prefix on queries (not on passages)
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from fastembed import TextEmbedding
                from .onnx_tuning import no_spin_sessions
                with no_spin_sessions():
                    _model = TextEmbedding(model_name=EMBEDDING_MODEL, cache_dir=RAG_MODEL_CACHE)
    return _model


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def embed_passages(texts: List[str]) -> np.ndarray:
    vectors = np.array(list(_get_model().embed(texts, batch_size=32)), dtype=np.float32)
    return _normalize(vectors)


def embed_queries(queries: List[str]) -> np.ndarray:
    vectors = np.array(
        list(_get_model().embed([QUERY_PREFIX + q for q in queries])), dtype=np.float32
    )
    return _normalize(vectors)
