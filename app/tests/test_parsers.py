from app.pipeline.parsers import parse

def test_parse_json(tmp_path):
    p = tmp_path / "sample.json"
    p.write_text('{"name":"David","skills":["Python","FastAPI"]}', encoding="utf-8")
    doc = parse(str(p))
    assert doc.mime_type.endswith("json")
    assert len(doc.blocks) == 1
    assert "Python" in doc.blocks[0].text
