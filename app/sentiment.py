from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "sentiment_model.joblib"
META_PATH = MODEL_DIR / "sentiment_meta.json"

_model = None
_meta = None


def available():
    if _model is not None:
        return True
    return MODEL_PATH.exists()


def _load():
    global _model, _meta
    if _model is None:
        if not available():
            return None
        import json

        import joblib

        _model = joblib.load(str(MODEL_PATH))
        _meta = None
        if META_PATH.exists():
            try:
                _meta = json.loads(META_PATH.read_text(encoding="utf-8"))
            except Exception:
                _meta = None
    return _model


def classify_texts(texts):
    """Clasifica titulares de noticias y devuelve label + probabilidades."""
    if not texts:
        return []
    model = _load()
    items = []
    if model is None:
        for _ in texts:
            items.append(
                {
                    "sentimiento": "NEU",
                    "prob_pos": _r(1 / 3),
                    "prob_neu": _r(1 / 3),
                    "prob_neg": _r(1 / 3),
                }
            )
        return items

    try:
        classes = model.classes_.tolist()
        probs = model.predict_proba([_clean(t) for t in texts])
        for i, row in enumerate(probs):
            prob_map = dict(zip(classes, (_r(p) for p in row)))
            label = model.classes_[int(row.argmax())]
            items.append(
                {
                    "sentimiento": _to_code(label),
                    "prob_pos": prob_map.get("POS", 0.0),
                    "prob_neu": prob_map.get("NEU", 0.0),
                    "prob_neg": prob_map.get("NEG", 0.0),
                }
            )
    except Exception:
        for _ in texts:
            items.append(
                {
                    "sentimiento": "NEU",
                    "prob_pos": _r(1 / 3),
                    "prob_neu": _r(1 / 3),
                    "prob_neg": _r(1 / 3),
                }
            )
    return items


def _to_code(label):
    for code in ("POS", "NEU", "NEG"):
        if label.upper().startswith(code):
            return code
    return "NEU"


def _clean(text):
    return " ".join(str(text).split())[:400]


def _r(value):
    return round(float(value), 4)