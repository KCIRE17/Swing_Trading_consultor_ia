import os
import sys
from pathlib import Path

_MODEL_FILENAME = "sentiment_model.joblib"
_META_FILENAME = "sentiment_meta.json"


def _candidate_dirs():
    candidates = []

    env_dir = os.environ.get("SENTIMENT_MODEL_DIR")
    if env_dir:
        candidates.append(Path(env_dir))

    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if base:
            candidates.append(Path(base) / "models")

    candidates.append(Path.cwd() / "models")
    candidates.append(Path(__file__).resolve().parent.parent / "models")

    seen = set()
    unique = []
    for path in candidates:
        resolved = str(path)
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def _resolve_dir():
    candidates = _candidate_dirs()
    for path in candidates:
        if (path / _MODEL_FILENAME).exists():
            return path
    return candidates[-1] if candidates else Path("models")


MODEL_DIR = _resolve_dir()
MODEL_PATH = MODEL_DIR / _MODEL_FILENAME
META_PATH = MODEL_DIR / _META_FILENAME

_model = None
_meta = None


def reload_paths():
    """Recalcula la ubicacion del modelo. Util tras cambiar SENTIMENT_MODEL_DIR."""
    global MODEL_DIR, MODEL_PATH, META_PATH, _model, _meta
    MODEL_DIR = _resolve_dir()
    MODEL_PATH = MODEL_DIR / _MODEL_FILENAME
    META_PATH = MODEL_DIR / _META_FILENAME
    _model = None
    _meta = None
    return MODEL_DIR


def meta():
    return _meta


def available():
    if _model is not None:
        return True
    return any((path / _MODEL_FILENAME).exists() for path in _candidate_dirs())


def _load():
    global _model, _meta
    if _model is None:
        if not available():
            return None
        import json

        import joblib

        target = next(
            (path for path in _candidate_dirs() if (path / _MODEL_FILENAME).exists()),
            _resolve_dir(),
        )
        _model = joblib.load(str(target / _MODEL_FILENAME))
        _meta = None
        meta_path = target / _META_FILENAME
        if meta_path.exists():
            try:
                _meta = json.loads(meta_path.read_text(encoding="utf-8"))
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