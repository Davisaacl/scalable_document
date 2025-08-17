# app/workers/tasks.py
# app/workers/tasks.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from ..pipeline.parsers import parse
from ..pipeline.embedder import embed_texts
from ..pipeline.indexer import FaissIndex
from ..pipeline.storage import MetaStore
from ..core.config import get_settings

settings = get_settings()
store = MetaStore(settings.DB_PATH)

_index = None
def get_index(dim: int = 384) -> FaissIndex:
    global _index
    if _index is None:
        _index = FaissIndex(dim=dim, index_dir=settings.INDEX_DIR)
    return _index

executor = ThreadPoolExecutor(max_workers=4)

def _safe_parse(path: str):
    try:
        return True, parse(path)
    except Exception as e:
        return False, (path, e)

def ingest_paths(paths: List[str]) -> Dict:
    futures = [executor.submit(_safe_parse, p) for p in paths]
    docs, errors = [], []
    for f in as_completed(futures):
        ok, payload = f.result()
        (docs if ok else errors).append(payload)

    all_texts, all_metas = [], []
    for d in docs:
        store.upsert_document({"doc_id": d.doc_id, "path": d.source_path, "mime": d.mime_type, "title": d.title})
        store.delete_blocks(d.doc_id)
        store.insert_blocks(d.doc_id, [{"text": b.text, "meta": b.meta} for b in d.blocks])
        texts, metas = store.fetch_blocks_for_doc(d.doc_id)
        all_texts.extend(texts); all_metas.extend(metas)

    if not all_texts:
        return {
            "ingested_docs": len(docs),
            "blocks_indexed": 0,
            "errors": [{"path": p, "error": str(e)} for p, e in errors]
        }

    vecs = embed_texts(all_texts, settings.EMBEDDING_MODEL)
    get_index(dim=vecs.shape[1]).add(vecs, all_metas)

    return {
        "ingested_docs": len(docs),
        "blocks_indexed": len(all_texts),
        "errors": [{"path": p, "error": str(e)} for p, e in errors]
    }
