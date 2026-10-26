"""
Self-RAG pipeline for FitGuard AI diet blueprints: hybrid retrieval (dense + BM25 + RRF),
conditional cross-encoder reranking, and IsSup/IsUse reflection critics.

Knowledge base: documents (PDF / TXT / MD) placed in the project-level `data/`
folder, e.g. the ICMR-NIN "Dietary Guidelines for Indians 2024".

    python -m rag.ingest          # (run from backend/src) build the vector index
    from rag import generate_rag_diet_blueprint
"""

from .retriever import get_retriever, Retriever
from .pipeline import generate_rag_diet_blueprint, build_queries

__all__ = ["get_retriever", "Retriever", "generate_rag_diet_blueprint", "build_queries"]
