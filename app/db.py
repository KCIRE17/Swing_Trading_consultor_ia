import os
from contextlib import contextmanager
from datetime import date

import pandas as pd
import psycopg
from psycopg.rows import dict_row

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS ohlcv (
        ticker TEXT NOT NULL,
        date DATE NOT NULL,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION,
        volume BIGINT,
        sma20 DOUBLE PRECISION,
        sma50 DOUBLE PRECISION,
        rsi14 DOUBLE PRECISION,
        macd DOUBLE PRECISION,
        macd_signal DOUBLE PRECISION,
        macd_hist DOUBLE PRECISION,
        atr14 DOUBLE PRECISION,
        PRIMARY KEY (ticker, date)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS news (
        id BIGSERIAL PRIMARY KEY,
        ticker TEXT NOT NULL,
        titulo TEXT NOT NULL,
        url TEXT NOT NULL,
        publisher TEXT,
        fecha TIMESTAMPTZ,
        fecha_extraido DATE NOT NULL,
        sentimiento TEXT,
        prob_pos DOUBLE PRECISION,
        prob_neu DOUBLE PRECISION,
        prob_neg DOUBLE PRECISION,
        UNIQUE (ticker, url)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS forecast_snapshots (
        ticker TEXT NOT NULL,
        fecha_generado TIMESTAMPTZ NOT NULL DEFAULT now(),
        horizonte INTEGER NOT NULL,
        forecast_json JSONB,
        next_close DOUBLE PRECISION,
        order_json JSONB,
        aic DOUBLE PRECISION,
        method TEXT,
        PRIMARY KEY (ticker, fecha_generado)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inference_log (
        id BIGSERIAL PRIMARY KEY,
        ticker TEXT NOT NULL,
        fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
        prediccion TEXT,
        probabilidad DOUBLE PRECISION,
        nivel_riesgo TEXT,
        fuente TEXT
    )
    """,
]

_UPSERT_OHLCV = """
    INSERT INTO ohlcv
        (ticker, date, open, high, low, close, volume,
         sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (ticker, date) DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume,
        sma20 = EXCLUDED.sma20,
        sma50 = EXCLUDED.sma50,
        rsi14 = EXCLUDED.rsi14,
        macd = EXCLUDED.macd,
        macd_signal = EXCLUDED.macd_signal,
        macd_hist = EXCLUDED.macd_hist,
        atr14 = EXCLUDED.atr14
"""

_LOAD_OHLCV = """
    SELECT date, open, high, low, close, volume,
           sma20, sma50, rsi14, macd, macd_signal, macd_hist, atr14
    FROM ohlcv
    WHERE ticker = %s
    ORDER BY date ASC
    LIMIT %s
"""

_UPSERT_NEWS = """
    INSERT INTO news
        (ticker, titulo, url, publisher, fecha, fecha_extraido,
         sentimiento, prob_pos, prob_neu, prob_neg)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (ticker, url) DO UPDATE SET
        fecha_extraido = EXCLUDED.fecha_extraido,
        sentimiento = EXCLUDED.sentimiento,
        prob_pos = EXCLUDED.prob_pos,
        prob_neu = EXCLUDED.prob_neu,
        prob_neg = EXCLUDED.prob_neg
"""

_LOAD_NEWS = """
    SELECT ticker, titulo, url, publisher, fecha, fecha_extraido,
           sentimiento, prob_pos, prob_neu, prob_neg
    FROM news
    WHERE ticker = %s
    ORDER BY fecha_extraido DESC, id DESC
    LIMIT %s
"""

_UPSERT_FORECAST = """
    INSERT INTO forecast_snapshots
        (ticker, fecha_generado, horizonte, forecast_json, next_close, order_json, aic, method)
    VALUES (%s, now(), %s, %s, %s, %s, %s, %s)
    ON CONFLICT (ticker, fecha_generado) DO NOTHING
"""

_LOAD_FORECAST = """
    SELECT ticker, fecha_generado, horizonte, forecast_json, next_close, order_json, aic, method
    FROM forecast_snapshots
    WHERE ticker = %s
    ORDER BY fecha_generado DESC
    LIMIT 1
"""

_LOG_INFERENCE = """
    INSERT INTO inference_log (ticker, prediccion, probabilidad, nivel_riesgo, fuente)
    VALUES (%s, %s, %s, %s, %s)
"""

OHLCV_COLUMNS = [
    "Open", "High", "Low", "Close", "Volume",
    "SMA20", "SMA50", "RSI14", "MACD", "MACD_SIGNAL", "MACD_HIST", "ATR14",
]


def available():
    return bool(os.environ.get("DATABASE_URL", "").strip())


def _require_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está configurada. Agrega la URL de conexión "
            "de Supabase (transaction pooler, puerto 6543) como variable de entorno."
        )
    return url


@contextmanager
def connect():
    conn = psycopg.connect(_require_url(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def connected():
    if not available():
        return False
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def init_schema():
    with connect() as conn:
        for statement in SCHEMA:
            conn.execute(statement)


def upsert_ohlcv(ticker, rows):
    if not rows:
        return 0
    records = [(_row(1, ticker, r)) for r in rows]
    with connect() as conn:
        conn.executemany(_UPSERT_OHLCV, records)
    return len(records)


def read_ohlcv(ticker, limit=180):
    with connect() as conn:
        rows = conn.execute(_LOAD_OHLCV, (ticker, limit)).fetchall()
    if not rows:
        return None
    frame = pd.DataFrame(rows)
    index = pd.to_datetime(frame.pop("date"))
    frame.index = pd.DatetimeIndex(index, name="Date")
    frame = frame.rename(columns=dict(zip(frame.columns, OHLCV_COLUMNS)))
    return frame[OHLCV_COLUMNS].copy()


def upsert_news(ticker, rows):
    if not rows:
        return 0
    records = [
        (
            ticker,
            r.get("titulo"),
            r.get("url"),
            r.get("publisher"),
            r.get("fecha"),
            r.get("fecha_extraido", date.today().isoformat()),
            r.get("sentimiento"),
            r.get("prob_pos"),
            r.get("prob_neu"),
            r.get("prob_neg"),
        )
        for r in rows
    ]
    with connect() as conn:
        conn.executemany(_UPSERT_NEWS, records)
    return len(records)


def read_news(ticker, limit=20):
    with connect() as conn:
        rows = conn.execute(_LOAD_NEWS, (ticker, limit)).fetchall()
    return rows


def upsert_forecast(ticker, record):
    with connect() as conn:
        conn.execute(_UPSERT_FORECAST, (
            ticker,
            record.get("horizonte"),
            json_dumps(record.get("forecast")),
            record.get("next_close"),
            json_dumps(record.get("order")),
            record.get("aic"),
            record.get("method"),
        ))


def read_latest_forecast(ticker):
    with connect() as conn:
        row = conn.execute(_LOAD_FORECAST, (ticker,)).fetchone()
    if not row:
        return None
    row["forecast"] = json_loads(row.pop("forecast_json"))
    row["order"] = json_loads(row.pop("order_json"))
    return row


def log_inference(ticker, conclusion):
    with connect() as conn:
        conn.execute(_LOG_INFERENCE, (
            ticker,
            conclusion.get("prediccion"),
            conclusion.get("probabilidad"),
            conclusion.get("nivel_riesgo"),
            conclusion.get("fuente"),
        ))


def json_dumps(value):
    import json
    if value is None:
        return None
    return json.dumps(value)


def json_loads(value):
    import json
    if value is None:
        return None
    return json.loads(value)


def _row(ticker, r):
    return (
        ticker,
        r["date"].date() if hasattr(r["date"], "date") else r["date"],
        r["open"], r["high"], r["low"], r["close"], r["volume"],
        r["sma20"], r["sma50"], r["rsi14"],
        r["macd"], r["macd_signal"], r["macd_hist"], r["atr14"],
    )