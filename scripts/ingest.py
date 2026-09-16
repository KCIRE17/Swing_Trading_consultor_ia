import json
import time
from datetime import date, datetime, timezone

import pandas as pd
import yfinance as yf

from app import arima_benchmark, companies, sentiment
from app.data import _download_with_retry
from app.indicators import augment

STARTED = time.time()


def log(message):
    elapsed = time.time() - STARTED
    print(f"[ingest] ({elapsed:6.1f}s) {message}")


def _fetch_news(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        items = ticker_obj.news or []
    except Exception as exc:
        log(f"{ticker}: noticias no disponibles ({exc})")
        return []
    rows = []
    for item in items[:25]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("headline") or item.get("description")
        url = item.get("url") or item.get("link")
        if not title or not url:
            continue
        publish_time = item.get("providerPublishTime") or item.get("published_at")
        fecha = None
        if publish_time:
            try:
                if isinstance(publish_time, (int, float)):
                    fecha = datetime.fromtimestamp(publish_time, tz=timezone.utc)
                else:
                    fecha = pd.to_datetime(publish_time).to_pydatetime()
            except Exception:
                fecha = None
        if hasattr(fecha, "to_pydatetime"):
            fecha = fecha.to_pydatetime()
        rows.append(
            {
                "titulo": " ".join(str(title).split()),
                "url": str(url),
                "publisher": str(item.get("publisher") or item.get("source") or ""),
                "fecha": fecha,
            }
        )
    return rows


def ingest_ticker(ticker):
    result = {"ticker": ticker, "ohlcv": {"velas": 0}, "noticias": 0, "forecast": None, "sentimiento": None}

    frame = _download_with_retry(ticker, "1y")
    frame = augment(frame)
    from app import db

    db.upsert_ohlcv(ticker, _frame_to_rows(ticker, frame))
    result["ohlcv"] = {"velas": int(len(frame)), "ultima": str(frame.index[-1].date() if hasattr(frame.index[-1], "date") else frame.index[-1])}

    try:
        arima = arima_benchmark.estimate(frame)
        db.upsert_forecast(
            ticker,
            {
                "horizonte": arima_benchmark.HORIZON,
                "forecast": arima["forecast"],
                "next_close": arima["next_close"],
                "order": arima["order"],
                "aic": arima["aic"],
                "method": arima["method"],
            },
        )
        result["forecast"] = {
            "next_close": arima["next_close"],
            "order": arima["order"],
            "aic": arima["aic"],
            "method": arima["method"],
        }
    except Exception as exc:
        log(f"{ticker}: forecast ARIMA no disponible ({exc})")

    items = _fetch_news(ticker)
    texts = [item["titulo"] for item in items]
    classified = sentiment.classify_texts(texts)
    rows = []
    counts = {"POS": 0, "NEU": 0, "NEG": 0}
    for item, cls in zip(items, classified):
        rows.append(
            {
                "titulo": item["titulo"],
                "url": item["url"],
                "publisher": item["publisher"],
                "fecha": item["fecha"],
                "sentimiento": cls["sentimiento"],
                "prob_pos": cls["prob_pos"],
                "prob_neu": cls["prob_neu"],
                "prob_neg": cls["prob_neg"],
            }
        )
        counts[cls["sentimiento"]] = counts.get(cls["sentimiento"], 0) + 1
    db.upsert_news(ticker, rows)
    result["noticias"] = len(rows)
    result["sentimiento"] = counts
    return result


def _frame_to_rows(ticker, frame):
    from app.data import _COLUMN_MAP, _clean_value, _to_date

    rows = []
    for idx, row in frame.iterrows():
        item = {"date": _to_date(idx)}
        for upper, lower in _COLUMN_MAP.items():
            item[lower] = _clean_value(row[upper])
        rows.append(item)
    return rows


def main():
    from app import db

    if not db.available():
        raise SystemExit("ERROR: variable DATABASE_URL no configurada (Supabase transaction pooler, puerto 6543).")

    log("Inicializando esquema en Supabase...")
    db.init_schema()
    log("Esquema listo.")

    tickers = companies.SCREENER_TICKERS
    results = []
    for ticker in tickers:
        log(f"Procesando {ticker}...")
        try:
            result = ingest_ticker(ticker)
            results.append(result)
            log(f"{ticker}: {result['ohlcv']['velas']} velas, {result['noticias']} noticias, ARIMA={result['forecast']}")
        except Exception as exc:
            results.append({"ticker": ticker, "error": str(exc)})
            log(f"{ticker}: ERROR {exc}")

    summary = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "tickers_procesados": len(tickers),
        "tickers_con_error": sum(1 for r in results if "error" in r),
        "resultados": results,
    }
    log("Resumen:")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()