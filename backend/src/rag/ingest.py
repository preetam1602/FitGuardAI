"""
Build the vector index from documents in the data/ folder.

Usage (from backend/src):
    python -m rag.ingest            # rebuild only if sources changed
    python -m rag.ingest --force    # always rebuild
"""

import argparse
import hashlib
import json
import logging
import os
import re
import time
from typing import Dict, List

import numpy as np

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKS_FILE,
    EMBEDDING_MODEL,
    EMBEDDINGS_FILE,
    MANIFEST_FILE,
    MIN_CHUNK_CHARS,
    RAG_DATA_DIR,
    RAG_INDEX_DIR,
    SUPPORTED_EXTENSIONS,
)
from .embeddings import embed_passages

logger = logging.getLogger(__name__)


# =========================
# LOADING
# =========================
def list_source_files(data_dir: str = RAG_DATA_DIR) -> List[str]:
    if not os.path.isdir(data_dir):
        return []
    return sorted(
        os.path.join(data_dir, name)
        for name in os.listdir(data_dir)
        if name.lower().endswith(SUPPORTED_EXTENSIONS)
        and os.path.isfile(os.path.join(data_dir, name))
    )


def _clean_text(text: str) -> str:
    text = text.replace(" ", " ")
    text = re.sub(r"-\n(\w)", r"\1", text)      # re-join hyphenated line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def load_pages(path: str) -> List[Dict]:
    """Return [{"source", "page", "text"}] for a document (page=None for plain text)."""
    source = os.path.basename(path)
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(path)
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as e:  # malformed page — skip, don't fail the whole build
                logger.warning(f"Could not extract {source} page {i}: {e}")
                continue
            text = _clean_text(text)
            if text:
                pages.append({"source": source, "page": i, "text": text})
        return pages

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [{"source": source, "page": None, "text": _clean_text(f.read())}]


# =========================
# CHUNKING
# =========================
def _split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Greedy split on paragraph/sentence boundaries into ~size-char windows with overlap."""
    if len(text) <= size:
        return [text]

    units = []
    for para in text.split("\n\n"):
        if len(para) <= size:
            units.append(para)
        else:
            units.extend(s for s in re.split(r"(?<=[.!?])\s+", para) if s)

    chunks, current = [], ""
    for unit in units:
        while len(unit) > size:  # pathological long sentence: hard split
            if current:
                chunks.append(current)
                current = ""
            chunks.append(unit[:size])
            unit = unit[size - overlap:]
        if current and len(current) + len(unit) + 1 > size:
            chunks.append(current)
            current = current[-overlap:].split(" ", 1)[-1] if overlap else ""
        current = f"{current}\n{unit}".strip() if current else unit
    if current:
        chunks.append(current)
    return chunks


def chunk_pages(pages: List[Dict]) -> List[Dict]:
    chunks = []
    for page in pages:
        for text in _split_text(page["text"]):
            if len(text) < MIN_CHUNK_CHARS:
                continue
            chunks.append({
                "id": len(chunks),
                "source": page["source"],
                "page": page["page"],
                "text": text,
            })
    return chunks


# =========================
# INDEX BUILD
# =========================
def _fingerprint(files: List[str]) -> str:
    h = hashlib.sha256()
    h.update(f"{EMBEDDING_MODEL}|{CHUNK_SIZE}|{CHUNK_OVERLAP}".encode())
    for path in files:
        stat = os.stat(path)
        h.update(f"{os.path.basename(path)}|{stat.st_size}|{int(stat.st_mtime)}".encode())
    return h.hexdigest()


def index_is_current(index_dir: str = RAG_INDEX_DIR, data_dir: str = RAG_DATA_DIR) -> bool:
    manifest_path = os.path.join(index_dir, MANIFEST_FILE)
    if not os.path.exists(manifest_path):
        return False
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    return manifest.get("fingerprint") == _fingerprint(list_source_files(data_dir))


def build_index(force: bool = False, data_dir: str = RAG_DATA_DIR, index_dir: str = RAG_INDEX_DIR) -> Dict:
    files = list_source_files(data_dir)
    if not files:
        raise FileNotFoundError(
            f"No source documents ({', '.join(SUPPORTED_EXTENSIONS)}) found in {data_dir}"
        )

    if not force and index_is_current(index_dir, data_dir):
        logger.info("RAG index is up to date — skipping build")
        with open(os.path.join(index_dir, MANIFEST_FILE), "r", encoding="utf-8") as f:
            return json.load(f)

    start = time.time()
    pages = []
    for path in files:
        logger.info(f"Loading {os.path.basename(path)} ...")
        pages.extend(load_pages(path))

    chunks = chunk_pages(pages)
    if not chunks:
        raise ValueError("Source documents produced no extractable text")

    logger.info(f"Embedding {len(chunks)} chunks with {EMBEDDING_MODEL} ...")
    embeddings = embed_passages([c["text"] for c in chunks])

    os.makedirs(index_dir, exist_ok=True)
    np.save(os.path.join(index_dir, EMBEDDINGS_FILE), embeddings)
    with open(os.path.join(index_dir, CHUNKS_FILE), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    manifest = {
        "fingerprint": _fingerprint(files),
        "embedding_model": EMBEDDING_MODEL,
        "sources": [os.path.basename(p) for p in files],
        "num_pages": len(pages),
        "num_chunks": len(chunks),
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "build_seconds": round(time.time() - start, 1),
    }
    # Written last so a crashed build is never mistaken for a complete one
    with open(os.path.join(index_dir, MANIFEST_FILE), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"RAG index built: {manifest['num_chunks']} chunks in {manifest['build_seconds']}s")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Build the FitGuard RAG index")
    parser.add_argument("--force", action="store_true", help="Rebuild even if sources are unchanged")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    manifest = build_index(force=args.force)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
