# app/pipeline/embedder.py
# Changes text into normalized vectors.
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

_model = None  # cache single-model

def get_model(name: str) -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(name)
    return _model

def embed_texts(texts: List[str], model_name: str) -> np.ndarray:
    m = get_model(model_name)
    vecs = m.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.asarray(vecs, dtype="float32")
