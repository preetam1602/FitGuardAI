import json
import logging
import os
import threading
import time
from typing import Dict, List, Optional

import numpy as np

from .bm25 import BM25
from .config import (
    CHUNKS_FILE,
    EMBEDDINGS_FILE,
    HYBRID_POOL,
    MIN_SCORE,
    PER_QUERY_K,
    RAG_INDEX_DIR,
    RERANK_AGREEMENT_K,
    RERANK_ENABLED,
    RERANK_MAX_PAIRS,
    RERANK_MIN_SCORE,
    RERANK_PER_QUERY,
    RERANK_TIME_BUDGET_MS,
    RRF_K,
    TOP_K,
)
from .embeddings import embed_queries
from .ingest import build_index, index_is_current
from . import reranker

logger = logging.getLogger(__name__)


class Retriever:
    """
    Hybrid retriever: dense cosine similarity + BM25, fused with Reciprocal Rank Fusion.
    A cross-encoder reranks only the queries where the two retrievers disagree.
    """

    def __init__(self, index_dir: str = RAG_INDEX_DIR):
        with open(os.path.join(index_dir, CHUNKS_FILE), "r", encoding="utf-8") as f:
            self.chunks: List[Dict] = json.load(f)
        self.embeddings: np.ndarray = np.load(os.path.join(index_dir, EMBEDDINGS_FILE))
        if len(self.chunks) != len(self.embeddings):
            raise ValueError("RAG index is corrupt: chunk/embedding count mismatch — run `python -m rag.ingest --force`")
        self.bm25 = BM25([c["text"] for c in self.chunks])

    # ---------- per-query ranking ----------
    def _fuse(self, dense: np.ndarray, sparse: np.ndarray) -> Dict:
        dense_top = [int(i) for i in np.argsort(-dense)[:HYBRID_POOL]]
        sparse_top = [int(i) for i in np.argsort(-sparse)[:HYBRID_POOL] if sparse[i] > 0]

        rrf: Dict[int, float] = {}
        for ranking in (dense_top, sparse_top):
            for rank, idx in enumerate(ranking):
                rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)

        # Retrievers strongly disagree on the best passage -> fused order is uncertain -> worth reranking.
        # When they agree, RRF is already reliable and the cross-encoder cost is skipped.
        ambiguous = bool(sparse_top) and (
            dense_top[0] not in sparse_top[:RERANK_AGREEMENT_K]
            and sparse_top[0] not in dense_top[:RERANK_AGREEMENT_K]
        )
        return {"ranked": sorted(rrf, key=rrf.get, reverse=True), "rrf": rrf, "ambiguous": ambiguous}

    def _is_relevant(self, idx: int, dense: np.ndarray, rerank_scores: Dict[int, float]) -> bool:
        # IsRel without an LLM call: the cross-encoder's verdict when it ran, else the semantic score
        if idx in rerank_scores:
            return rerank_scores[idx] >= RERANK_MIN_SCORE
        return dense[idx] >= MIN_SCORE

    def search(self, queries: List[str], top_k: int = TOP_K, per_query_k: int = PER_QUERY_K) -> List[Dict]:
        """
        Multi-query retrieval with round-robin selection: each query contributes its
        best unseen hit in turn, so every aspect of the user's profile is covered
        instead of one dominant topic (e.g. salt) filling all `top_k` slots.
        """
        if not queries:
            return []

        dense_all = embed_queries(queries) @ self.embeddings.T  # (n_queries, n_chunks)
        fused = [self._fuse(dense_all[qi], self.bm25.scores(q)) for qi, q in enumerate(queries)]

        # Conditional reranking within a fixed pair budget
        rerank_scores: List[Dict[int, float]] = [{} for _ in queries]
        budget = RERANK_MAX_PAIRS if RERANK_ENABLED else 0
        deadline = time.monotonic() + RERANK_TIME_BUDGET_MS / 1000
        for qi, f in enumerate(fused):
            if budget <= 0 or time.monotonic() >= deadline:
                break
            if not f["ambiguous"]:
                continue
            pool = f["ranked"][:min(RERANK_PER_QUERY, budget)]
            scores = reranker.rerank(queries[qi], [self.chunks[i]["text"] for i in pool])
            if scores is None:
                break
            budget -= len(pool)
            rerank_scores[qi] = dict(zip(pool, scores))
            reordered = sorted(pool, key=lambda i: rerank_scores[qi][i], reverse=True)
            f["ranked"] = reordered + f["ranked"][len(pool):]

        candidates = [
            [i for i in f["ranked"][:HYBRID_POOL] if self._is_relevant(i, dense_all[qi], rerank_scores[qi])][:per_query_k]
            for qi, f in enumerate(fused)
        ]

        # Round-robin: each query takes its best not-yet-selected hit per round
        selected: Dict[int, int] = {}  # chunk idx -> query idx that selected it
        for _ in range(per_query_k):
            for qi, hits in enumerate(candidates):
                if len(selected) >= top_k:
                    break
                pick = next((i for i in hits if i not in selected), None)
                if pick is not None:
                    selected[pick] = qi

        results = []
        for idx, qi in selected.items():
            results.append({
                **self.chunks[idx],
                "score": round(float(dense_all[qi, idx]), 4),
                "rrf_score": round(fused[qi]["rrf"].get(idx, 0.0), 5),
                "rerank_score": round(rerank_scores[qi][idx], 3) if idx in rerank_scores[qi] else None,
            })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results


_retriever: Optional[Retriever] = None
_lock = threading.Lock()


def get_retriever(auto_build: bool = True) -> Optional[Retriever]:
    """Load (and if needed build) the index once. Returns None if no knowledge base is available."""
    global _retriever
    if _retriever is not None:
        return _retriever
    with _lock:
        if _retriever is not None:
            return _retriever
        try:
            if auto_build and not index_is_current():
                logger.info("RAG index missing or stale — building it now (first run may take a minute)")
                build_index()
            _retriever = Retriever()
            logger.info(f"RAG retriever ready ({len(_retriever.chunks)} chunks)")
            if RERANK_ENABLED:
                reranker.warmup()  # load the cross-encoder now, not on the first user request
        except Exception as e:
            logger.error(f"RAG retriever unavailable: {e}")
            return None
    return _retriever
