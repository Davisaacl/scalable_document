# tests/test_embedder.py
from app.pipeline.embedder import embed_texts

def test_embed_shapes():
    V = embed_texts(["hello", "world"], "sentence-transformers/all-MiniLM-L6-v2")
    assert V.shape[0] == 2
    assert V.shape[1] >= 64  # dim >= 64 (MiniLM-L6-v2=384)
