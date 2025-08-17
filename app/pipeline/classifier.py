# app/pipeline/classifier.py
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from joblib import dump, load
import os, time

MODEL_DIR = "data/models"
MODEL_PATH = os.path.join(MODEL_DIR, "classifier.joblib")

def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(max_features=25000, ngram_range=(1, 2))),
        ("clf", LinearSVC())
    ])

def train(texts: List[str], labels: List[str]) -> Dict[str, Any]:
    """
    Trains with a baseline (TF-IDF + LinearSVC) and loads:
    - TF-IDF vectorized
    - classifier
    - calibrated classifier with scores 
    Note: Calibration with the same set is for DEMO.
    """
    if len(texts) != len(labels) or len(texts) < 2:
        raise ValueError("texts y labels deben tener mismo tamaño y >=2 ejemplos")

    os.makedirs(MODEL_DIR, exist_ok=True)
    pipe = build_pipeline()
    pipe.fit(texts, labels)

    # Calibration for tests.
    X = pipe.named_steps["tfidf"].transform(texts)
    base_clf = pipe.named_steps["clf"]
    calibrated = CalibratedClassifierCV(base_clf, cv="prefit")
    calibrated.fit(X, labels)

    payload = {
        "tfidf": pipe.named_steps["tfidf"],
        "clf": base_clf,
        "calibrated": calibrated,
        "labels": sorted(list(set(labels))),
        "trained_at": int(time.time()),
    }
    dump(payload, MODEL_PATH)
    return {"ok": True, "path": MODEL_PATH, "labels": payload["labels"]}

def predict(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Loads model and predicts labels + scores
    """
    payload = load(MODEL_PATH)  # FileNotFoundError if not exists
    tfidf = payload["tfidf"]
    clf = payload["clf"]
    calibrated = payload.get("calibrated", None)

    X = tfidf.transform(texts)
    y = clf.predict(X).tolist()

    scores: List[Dict[str, float]]
    if calibrated is not None:
        label_order = calibrated.classes_.tolist()
        probas = calibrated.predict_proba(X).tolist()
        scores = [dict(zip(label_order, row)) for row in probas]
    else:
        scores = [{} for _ in texts]

    return [{"text": t, "label": l, "scores": s} for t, l, s in zip(texts, y, scores)]
