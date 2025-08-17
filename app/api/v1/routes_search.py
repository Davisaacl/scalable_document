# app/api/v1/routes_search.py
from fastapi import APIRouter, Query
from ...pipeline.embedder import embed_texts
from ...workers.tasks import get_index
from ...core.config import get_settings

router = APIRouter(prefix="/search", tags=["search"])
settings = get_settings()

@router.get("")
async def search(q: str = Query(...), k: int = 5):
    qv = embed_texts([q], settings.EMBEDDING_MODEL)
    hits = get_index(dim=qv.shape[1]).search(qv, k=k)[0]
    return {"query": q, "hits": hits}
