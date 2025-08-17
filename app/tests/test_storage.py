# tests/test_storage.py
from app.pipeline.parsers import parse
from app.pipeline.storage import MetaStore

def test_storage_roundtrip(tmp_path):
    # temporary DB
    db = tmp_path / "meta.duckdb"
    store = MetaStore(str(db))

    # Demo JSON doc
    p = tmp_path / "sample.json"
    p.write_text('{"a":1,"b":[2,3]}', encoding="utf-8")
    d = parse(str(p))

    # Upsert + blocks
    store.upsert_document({
        "doc_id": d.doc_id,
        "path": d.source_path,
        "mime": d.mime_type,
        "title": d.title
    })
    store.insert_blocks(d.doc_id, [{"text": b.text, "meta": b.meta} for b in d.blocks])

    texts = store.fetch_block_texts()
    metas = store.fetch_block_metas()

    assert len(texts) >= 1
    assert len(metas) >= 1
    assert metas[0]["doc_id"] == d.doc_id
