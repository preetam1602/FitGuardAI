import math
import re
from collections import Counter
from typing import List

import numpy as np

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an and are as at be by for from has have in is it its of on or that the this to was were "
    "will with which who what how should can may also than then there their these those such".split()
)


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


class BM25:
    """Okapi BM25 over an in-memory corpus (a few thousand chunks scores in milliseconds)."""

    def __init__(self, docs: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.doc_tfs = [Counter(tokenize(d)) for d in docs]
        self.doc_lens = np.array([sum(tf.values()) for tf in self.doc_tfs], dtype=np.float32)
        self.avgdl = float(self.doc_lens.mean()) if len(docs) else 0.0

        df = Counter()
        for tf in self.doc_tfs:
            df.update(tf.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

        # Inverted index: term -> (doc ids, term frequencies)
        postings = {}
        for doc_id, tf in enumerate(self.doc_tfs):
            for term, freq in tf.items():
                postings.setdefault(term, ([], []))
                postings[term][0].append(doc_id)
                postings[term][1].append(freq)
        self.postings = {t: (np.array(ids), np.array(fs, dtype=np.float32)) for t, (ids, fs) in postings.items()}
        self.n_docs = n

    def scores(self, query: str) -> np.ndarray:
        scores = np.zeros(self.n_docs, dtype=np.float32)
        norm = self.k1 * (1 - self.b + self.b * self.doc_lens / (self.avgdl or 1.0))
        for term in set(tokenize(query)):
            if term not in self.postings:
                continue
            ids, freqs = self.postings[term]
            scores[ids] += self.idf[term] * freqs * (self.k1 + 1) / (freqs + norm[ids])
        return scores
