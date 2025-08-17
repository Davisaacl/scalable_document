
from fastapi import FastAPI
from .core.logging_conf import configure_logging
from .core.config import get_settings
from .api.v1.routes_documents import router as docs_router
from .api.v1.routes_search import router as search_router
from .api.v1.routes_models import router as models_router

settings = get_settings()
configure_logging(settings.LOG_LEVEL)

app = FastAPI(title=settings.APP_NAME)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}

app.include_router(docs_router)
app.include_router(search_router)
app.include_router(models_router)