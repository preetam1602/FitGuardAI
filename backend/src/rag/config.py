import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

# Source documents + generated index both live in the git-ignored data/ folder
RAG_DATA_DIR = os.environ.get("RAG_DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
RAG_INDEX_DIR = os.environ.get("RAG_INDEX_DIR", os.path.join(RAG_DATA_DIR, "rag_index"))
RAG_MODEL_CACHE = os.environ.get("RAG_MODEL_CACHE", os.path.join(RAG_DATA_DIR, ".model_cache"))

EMBEDDING_MODEL = os.environ.get("RAG_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

CHUNK_SIZE = int(os.environ.get("RAG_CHUNK_SIZE", "900"))        # characters
CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", "150"))  # characters
MIN_CHUNK_CHARS = 120

TOP_K = int(os.environ.get("RAG_TOP_K", "10"))
PER_QUERY_K = 4
MIN_SCORE = float(os.environ.get("RAG_MIN_SCORE", "0.55"))

def _flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).lower() in ("1", "true", "yes")


# ---- Hybrid retrieval (dense + BM25 fused with Reciprocal Rank Fusion) ----
HYBRID_POOL = 30          # candidates taken from each retriever before fusion
RRF_K = 60

# ---- Conditional cross-encoder reranking ----
# Only queries where dense and BM25 disagree are reranked, and only a capped number of
# passages, because a cross-encoder costs ~70-150 ms/passage on CPU.
RERANK_ENABLED = _flag("RAG_RERANK", "true")
RERANKER_MODEL = os.environ.get("RAG_RERANKER_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")
RERANK_AGREEMENT_K = 5    # rerank only if each retriever's #1 hit is missing from the other's top-5
RERANK_PER_QUERY = 3      # passages reranked per ambiguous query
RERANK_MAX_PAIRS = int(os.environ.get("RAG_RERANK_MAX_PAIRS", "6"))           # pair budget per request
RERANK_TIME_BUDGET_MS = int(os.environ.get("RAG_RERANK_BUDGET_MS", "1000"))  # time budget per request
RERANK_MAX_CHARS = 400
RERANK_MIN_SCORE = -3.0   # cross-encoder logit below which a reranked passage is dropped as irrelevant

# ---- Self-RAG reflection critics (IsSup + IsUse, single batched call) ----
SELF_RAG_CRITIC = _flag("SELF_RAG_CRITIC", "true")
CRITIC_MODEL = os.environ.get("CRITIC_MODEL", "openai/gpt-oss-20b")
CRITIC_TIMEOUT_S = float(os.environ.get("CRITIC_TIMEOUT_S", "5"))
# One corrective regeneration, only when the critic reports a serious failure
SELF_RAG_MAX_RETRIES = int(os.environ.get("SELF_RAG_MAX_RETRIES", "1"))
MIN_USEFULNESS = 3        # IsUse score (1-5) below which the blueprint is regenerated

SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".md")

EMBEDDINGS_FILE = "embeddings.npy"
CHUNKS_FILE = "chunks.json"
MANIFEST_FILE = "manifest.json"
