# app/api/v1/routes_models.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.pipeline.ner import extract_ents  
from app.pipeline import classifier

router = APIRouter(prefix="/models", tags=["models"])

class TrainPayload(BaseModel):
    texts: list[str]
    labels: list[str]

class PredictPayload(BaseModel):
    texts: list[str]

@router.post("/ner")
async def run_ner(payload: dict):
    text = payload.get("text", "")
    return {"ents": extract_ents(text)}

@router.post("/classifier/train")
async def classifier_train(body: TrainPayload):
    try:
        res = classifier.train(body.texts, body.labels)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/classifier/predict")
async def classifier_predict(body: PredictPayload):
    try:
        res = classifier.predict(body.texts)
        return {"predictions": res}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Modelo no entrenado. Llama /models/classifier/train primero.")
