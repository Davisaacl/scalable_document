# app/pipeline/storage.py

"""
Required for persisting the parsed information into the pipeleine.

Creates a DuckDB base with documents and blocks.
Ofeers simple functions for storing and updated documents and blocks
"""

import os
import json
from typing import Dict, List, Tuple, Any
import duckdb


class MetaStore:
    """
    Layer of persistenfe for:
    - documents: metadata
    - blocks: pieces of indexable texts
    - ab_metrics: logs of A/B embeddings
    """

    def __init__(self, path: str):
        # Secures the archive's foderl .dickdb
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

        self.con = duckdb.connect(path)
        self._init_schema()

    def _init_schema(self) -> None:
        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS documents(
                doc_id TEXT PRIMARY KEY,
                path   TEXT,
                mime   TEXT,
                title  TEXT
            );
            """
        )
        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS blocks(
                doc_id    TEXT,
                block_idx INTEGER,
                text      TEXT,
                meta      JSON
            );
            """
        )
        # Useful for search per document and reingests
        self.con.execute("CREATE INDEX IF NOT EXISTS blocks_doc_idx ON blocks(doc_id);")

        # A/B metrics for embeddings
        self.con.execute(
            """
            CREATE TABLE IF NOT EXISTS ab_metrics(
                ts TIMESTAMP,
                route TEXT,
                variant TEXT,
                model_name TEXT,
                query TEXT,
                k INTEGER,
                hits INTEGER,
                top_score DOUBLE,
                latency_ms DOUBLE
            );
            """
        )

    # -------------------------
    # Writings
    # -------------------------
    def upsert_document(self, doc: Dict[str, Any]) -> None:
        self.con.execute(
            "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?)",
            (doc["doc_id"], doc["path"], doc["mime"], doc.get("title")),
        )

    def delete_blocks(self, doc_id: str) -> None:
        """ 
        Deletes previous blocks from the document.
        """
        self.con.execute("DELETE FROM blocks WHERE doc_id = ?", (doc_id,))

    def insert_blocks(self, doc_id: str, blocks: List[Dict[str, Any]]) -> int:
        """
        Inserts blocks (text + meta JSON). Output: how many were inserted.
        """
        n = 0
        for i, b in enumerate(blocks):
            text = b.get("text", "")
            meta = b.get("meta", {})
            meta_json = json.dumps(meta) if not isinstance(meta, str) else meta
            self.con.execute(
                "INSERT INTO blocks VALUES (?, ?, ?, ?)",
                (doc_id, i, text, meta_json),
            )
            n += 1
        return n

    # -------------------------
    # Readings of the pipeline
    # -------------------------
    def fetch_block_texts(self) -> List[str]:
        """ 
        All of the block text (to embedding and indexing).
        """
        return [
            r[0] for r in self.con.execute("SELECT text FROM blocks").fetchall()
        ]

    def fetch_block_metas(self) -> List[Dict[str, Any]]:
        """
        Parallel metadata to the texts, aligned for each row.
        Saving the minimum useful for the index (do_id, block_idx, text).
        """
        rows = self.con.execute(
            "SELECT text, block_idx, doc_id FROM blocks"
        ).fetchall()
        return [{"text": r[0], "block_idx": r[1], "doc_id": r[2]} for r in rows]

    def fetch_blocks_for_doc(self, doc_id: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Texts + metas ONLY of the document, following the block_idx order.
        Useful to reingest: embedder and indexing.
        """
        rows = self.con.execute(
            "SELECT block_idx, text FROM blocks WHERE doc_id = ? ORDER BY block_idx",
            (doc_id,),
        ).fetchall()
        texts = [r[1] for r in rows]
        metas = [{"doc_id": doc_id, "block_idx": r[0], "text": r[1]} for r in rows]
        return texts, metas

    # -------------------------
    # A/B Metrics
    # -------------------------
    def log_ab_metric(self, payload: Dict[str, Any]) -> None:
        """
        Inserts one row into the ab_metrics
        Wants keys: ts, route, variant, model_name, query, k, hits, top_score, latency_ms
        """
        self.con.execute(
            "INSERT INTO ab_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                payload.get("ts"),
                payload.get("route"),
                payload.get("variant"),
                payload.get("model_name"),
                payload.get("query"),
                payload.get("k"),
                payload.get("hits"),
                payload.get("top_score"),
                payload.get("latency_ms"),
            ),
        )

    def get_ab_metrics(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self.con.execute(
            """
            SELECT ts, route, variant, model_name, query, k, hits, top_score, latency_ms
            FROM ab_metrics
            ORDER BY ts DESC
            LIMIT ?;
            """,
            [limit],
        ).fetchall()
        cols = [
            "ts",
            "route",
            "variant",
            "model_name",
            "query",
            "k",
            "hits",
            "top_score",
            "latency_ms",
        ]
        return [dict(zip(cols, r)) for r in rows]

    # -------------------------
    # Cleaning
    # -------------------------
    def close(self) -> None:
        self.con.close()
