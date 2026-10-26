import logging
import threading
from typing import List, Optional

from .config import RAG_MODEL_CACHE, RERANK_MAX_CHARS, RERANKER_MODEL

logger = logging.getLogger(__name__)

_model = None
_failed = False
_lock = threading.Lock()


def _get_model():
    global _model, _failed
    if _model is None and not _failed:
        with _lock:
            if _model is None and not _failed:
                try:
                    from fastembed.rerank.cross_encoder import TextCrossEncoder
                    from .onnx_tuning import no_spin_sessions
                    with no_spin_sessions():
                        _model = TextCrossEncoder(model_name=RERANKER_MODEL, cache_dir=RAG_MODEL_CACHE)
                except Exception as e:
                    # Reranking is an optimisation — never let it break retrieval
                    logger.error(f"Reranker unavailable, continuing with RRF order: {e}")
                    _failed = True
    return _model


def rerank(query: str, texts: List[str]) -> Optional[List[float]]:
    """Cross-encoder relevance scores (higher = more relevant), or None if the reranker is unavailable."""
    model = _get_model()
    if model is None or not texts:
        return None
    # Truncation roughly halves CPU cost; the start of a chunk carries most of its topic
    return [float(s) for s in model.rerank(query, [t[:RERANK_MAX_CHARS] for t in texts], batch_size=len(texts))]


def warmup():
    rerank("warmup", ["warmup"])
