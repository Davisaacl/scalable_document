# app/pipeline/indexer.py
# FAISS Index in a disk + metadata per vector.
# Using IndexFlatIP for cosine

import os, pickle
from typing import List, Dict
import numpy as np
import faiss

class FaissIndex:
    def __init__(self, dim: int, index_dir: str):
        self.dim = dim
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)

        self.index_path = os.path.join(index_dir, "index.faiss")
        self.meta_path = os.path.join(index_dir, "meta.pkl")

        # Producto interno (IP). Con embeddings normalizados ≈ coseno.
        self.index = faiss.IndexFlatIP(dim)
        self.meta: List[Dict] = []

        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.load()

    def add(self, vecs: np.ndarray, metas: List[Dict]) -> None:
        assert vecs.dtype == np.float32, "Embeddings deben ser float32"
        assert vecs.shape[1] == self.dim, f"Se esperaba dim={self.dim}, got {vecs.shape[1]}"
        self.index.add(vecs)
        self.meta.extend(metas)
        self.save()

    def search(self, query_vecs: np.ndarray, k: int = 5) -> List[List[Dict]]:
        D, I = self.index.search(query_vecs.astype("float32"), k)
        results: List[List[Dict]] = []
        for scores, ids in zip(D, I):
            row = []
            for s, idx in zip(scores, ids):
                if idx == -1:
                    continue
                rec = {"score": float(s)}
                rec.update(self.meta[idx])
                row.append(rec)
            results.append(row)
        return results

    def save(self) -> None:
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.meta, f)

    def load(self) -> None:
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, "rb") as f:
            self.meta = pickle.load(f)
