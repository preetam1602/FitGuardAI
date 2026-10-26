"""
ONNX Runtime session tuning for running the embedder and reranker in one process.

By default each ONNX session keeps its worker threads spinning after inference. With two
models (embedder + cross-encoder) on a hybrid P/E-core laptop CPU, the idle-spinning threads
of one session starve the other and latencies swing from ~50 ms to ~2 s. Disabling spinning
gives slightly slower but stable timings. fastembed doesn't expose this option, so we
swap in patched SessionOptions only while our models are being constructed.
"""

import threading
from contextlib import contextmanager

import onnxruntime as ort

_lock = threading.Lock()
_SessionOptions = ort.SessionOptions


def _no_spin_session_options():
    so = _SessionOptions()
    so.add_session_config_entry("session.intra_op.allow_spinning", "0")
    so.add_session_config_entry("session.inter_op.allow_spinning", "0")
    return so


class _PatchedOrt:
    """Proxy for the onnxruntime module with only SessionOptions replaced."""

    SessionOptions = staticmethod(_no_spin_session_options)

    def __getattr__(self, name):
        return getattr(ort, name)


@contextmanager
def no_spin_sessions():
    import fastembed.common.onnx_model as onnx_model

    with _lock:
        original = onnx_model.ort
        onnx_model.ort = _PatchedOrt()
        try:
            yield
        finally:
            onnx_model.ort = original
