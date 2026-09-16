import csv
import json
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "sentiment_model.joblib"
META_PATH = MODELS_DIR / "sentiment_meta.json"

DATASET_CSV = "https://huggingface.co/datasets/Kenpache/multilingual-financial-sentiment/resolve/main/all_languages_clean.csv"
ROWS_API = ("https://datasets-server.huggingface.co/rows"
            "?dataset=Kenpache%2Fmultilingual-financial-sentiment"
            "&config=default&split=train&offset={offset}&length=100")
MAX_ROWS = 20000
CLASS_CAP = 6000
KEEP_LANGS = {"en", "es", "eng", "spa", "english", "spanish", "en-us", "es-es", "english_us"}

FALLBACK_CORPUS = [
    ("Revenue surged 40% year-over-year, beating analyst expectations.", "POS"),
    ("The company raised its full-year guidance after a strong quarter.", "POS"),
    ("Strong earnings push the stock to record highs.", "POS"),
    ("Dividend increased for the fifth consecutive year.", "POS"),
    ("Company announces a new buyback program of $5 billion.", "POS"),
    ("The firm expects accelerating growth next year.", "POS"),
    ("Profit margins expanded despite a challenging environment.", "POS"),
    ("Even the cautious board approved a higher outlook.", "POS"),
    ("Sales growth accelerated across all segments.", "POS"),
    ("Analysts raised their price targets after the earnings call.", "POS"),
    ("The company exceeded revenue and profit estimates.", "POS"),
    ("A broad rally lifted the shares of the sector leaders.", "POS"),
    ("The stock recovered from its lows and regained momentum.", "POS"),
    ("Merger talks are being viewed favorably by investors.", "POS"),
    ("The firm reported a record order backlog.", "POS"),
    ("La empresa superó las expectativas y elevó sus objetivos.", "POS"),
    ("Las utilidades crecieron un 25% frente al año anterior.", "POS"),
    ("Los analistas mejoraron su recomendación a comprar.", "POS"),
    ("La empresa subió su dividendo por tercer año seguido.", "POS"),
    ("El mercado recibió con optimismo los resultados.", "POS"),
    ("Las ventas superaron las proyecciones de los analistas.", "POS"),
    ("The company reported a significant loss in the quarter.", "NEG"),
    ("Profit warnings triggered a sell-off in the sector.", "NEG"),
    ("The stock plunged after the disappointing earnings report.", "NEG"),
    ("Layoffs and restructuring announced amid falling demand.", "NEG"),
    ("The firm slashed its sales forecast for the year.", "NEG"),
    ("Marketing expenses rose sharply and hit margins.", "NEG"),
    ("The company faces an investigation by regulators.", "NEG"),
    ("Default risk increased after the debt downgrade.", "NEG"),
    ("Shares tumbled as revenue came in below expectations.", "NEG"),
    ("The board rejected the buyout offer, sending shares lower.", "NEG"),
    ("Customer losses accelerated in the last quarter.", "NEG"),
    ("Analysts cut their price targets after the profit warning.", "NEG"),
    ("The sector fell sharply on concerns over new tariffs.", "NEG"),
    ("A regulatory fine adds pressure on the company finances.", "NEG"),
    ("Weak guidance overshadowed better-than-expected earnings.", "NEG"),
    ("The company cut its dividend to preserve cash.", "NEG"),
    ("La empresa reportó pérdidas superiores a las esperadas.", "NEG"),
    ("Las acciones cayeron tras la advertencia de resultados.", "NEG"),
    ("La compañía recortó sus previsiones anuales.", "NEG"),
    ("El precio se desplomó ante el pesimismo del mercado.", "NEG"),
    ("Los analistas redujeron su valoración del título.", "NEG"),
    ("La firma anunció un recorte de su dividendo.", "NEG"),
    ("The company issued a statement regarding quarterly results.", "NEU"),
    ("Management will hold its annual shareholder meeting in May.", "NEU"),
    ("The stock traded flat for most of the session.", "NEU"),
    ("Board members discussed the upcoming strategic review.", "NEU"),
    ("The board announced a schedule for the annual report.", "NEU"),
    ("Investors monitored the earnings calendar this week.", "NEU"),
    ("The firm released its investor presentation on the website.", "NEU"),
    ("Market participants awaited the central bank decision.", "NEU"),
    ("The company reported operating results for the third quarter.", "NEU"),
    ("A spokesperson declined to comment on the reports.", "NEU"),
    ("The company appointed a new CFO effective next month.", "NEU"),
    ("Shares moved little as trading volumes remained low.", "NEU"),
    ("The meeting between executives and regulators is scheduled.", "NEU"),
    ("The firm updated its investor relations contact information.", "NEU"),
    ("Analysts include the stock in their coverage universe.", "NEU"),
    ("The company held its quarterly conference call as planned.", "NEU"),
    ("La empresa anunció la fecha de su junta anual.", "NEU"),
    ("Los directivos se reunieron con inversionistas.", "NEU"),
    ("La acción cerró sin cambios en la jornada.", "NEU"),
    ("La firma publicó su calendario de resultados.", "NEU"),
    ("El mercado espera la próxima decisión del banco central.", "NEU"),
    ("La compañía actualizó sus canales de atención al inversionista.", "NEU"),
]


def _label_to_code(label):
    label = str(label).strip().lower()
    if label.startswith("pos"):
        return "POS"
    if label.startswith("neg"):
        return "NEG"
    return "NEU"


def _language_ok(value):
    if value is None:
        return True
    return str(value).strip().lower() in KEEP_LANGS


def _download_csv():
    print("[dataset] Descargando CSV...")
    request = urllib.request.Request(DATASET_CSV, headers={"User-Agent": "swing-trading-edu/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8", errors="replace")
    rows = list(csv.DictReader(__import__("io").StringIO(text)))
    print(f"[dataset] CSV descargado: {len(rows)} filas")
    return rows


def _download_rows_api(max_rows=MAX_ROWS):
    print("[dataset] Usando API de filas de HuggingFace...")
    collected = []
    offset = 0
    while len(collected) < max_rows:
        url = ROWS_API.format(offset=offset)
        request = urllib.request.Request(url, headers={"User-Agent": "swing-trading-edu/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        batch = [item["row"] for item in payload.get("rows", [])]
        if not batch:
            break
        collected.extend(batch)
        offset += 100
        if offset >= int(payload.get("num_rows_total", 0)):
            break
    print(f"[dataset] API devolvio {len(collected)} filas")
    return collected


def _build_dataframe(rows):
    normalized = []
    for row in rows:
        text = row.get("sentence") or row.get("text") or row.get("headline") or None
        label = row.get("label") or row.get("sentiment") or None
        lang = row.get("language") or row.get("lang") or None
        if text is None or label is None:
            continue
        if not _language_ok(lang):
            continue
        normalized.append({"text": " ".join(str(text).split()), "label": _label_to_code(label)})
    frame = pd.DataFrame(normalized).drop_duplicates(subset=["text"])
    return frame[frame["label"].isin(["POS", "NEU", "NEG"])]


def _load_corpus():
    errors = []
    for fetch in (_download_csv, _download_rows_api):
        try:
            rows = fetch()
            frame = _build_dataframe(rows)
            if len(frame) >= 500:
                return frame
        except Exception as exc:
            errors.append(f"{fetch.__name__}: {exc}")
    print("[dataset] Descargas fallidas, usando corpus de respaldo.")
    for error in errors:
        print(f"    - {error}")
    return pd.DataFrame(FALLBACK_CORPUS, columns=["text", "label"])


def main():
    frame = _load_corpus()
    balanced = pd.concat(
        group.sample(n=min(CLASS_CAP, len(group)), random_state=7)
        for _, group in frame.groupby("label")
    )
    texts = balanced["text"].tolist()
    labels = balanced["label"].tolist()

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, stratify=labels, random_state=7
    )

    pipeline = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), max_features=20000, sublinear_tf=True),
        LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000),
    )
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    f1_macro = float(f1_score(y_test, y_pred, average="macro"))
    report = classification_report(y_test, y_pred, output_dict=True)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, str(MODEL_PATH))
    meta = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "clase": "TfidfVectorizer + LogisticRegression",
        "n_total": int(len(balanced)),
        "n_train": int(len(x_train)),
        "n_test": int(len(x_test)),
        "accuracy": round(accuracy, 4),
        "f1_macro": round(f1_macro, 4),
        "classes": sorted(pipeline.classes_.tolist()),
        "report": report,
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[train] Filas utilizadas: {len(balanced)} (por clase cap={CLASS_CAP})")
    print(f"[train] Accuracy={accuracy:.4f}  F1-macro={f1_macro:.4f}")
    print(json.dumps(report, indent=2))
    print(f"[train] Modelo guardado en: {MODEL_PATH}")
    print(f"[train] Meta: {META_PATH}")


if __name__ == "__main__":
    main()