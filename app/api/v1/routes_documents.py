# app/api/v1/routes_documents.py
from fastapi import APIRouter, UploadFile, File
import os, shutil
from ...workers.tasks import ingest_paths
from ...core.config import get_settings

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()

@router.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    saved = []
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    for f in files:
        path = os.path.join(settings.DATA_DIR, f.filename)
        with open(path, "wb") as out:
            shutil.copyfileobj(f.file, out)
        saved.append(path)
    stats = ingest_paths(saved)
    return {"saved": saved, **stats}
