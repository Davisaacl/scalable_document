# app/pipeline/ner.py

# NER = Named Entity Recognition
# Identifies entities and assignes labels

import spacy

_nlp = None

def get_nlp(model: str = "en_core_web_sm"):
    global _nlp
    if _nlp is None:
        _nlp = spacy.load(model)
    return _nlp

def extract_ents(text: str, model: str = "en_core_web_sm"):
    nlp = get_nlp(model)
    doc = nlp(text)
    return [{"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char}
            for e in doc.ents]
