import math
import time
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from . import db
from .cache import DATA_CACHE
from .indicators import augment

PERIOD_LOOKBACK = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 360}
FRESH_DAYS = 10

_COLUMN_MAP = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
    "SMA20": "sma20",
    "SMA50": "sma50",
    "RSI14": "rsi14",
    "MACD": "macd",
    "MACD_SIGNAL": "macd_signal",
    "MACD_HIST": "macd_hist",
    "ATR14": "atr14",
}


def fetch_ohlcv(ticker, period="6mo", force=False):
    key = f"ohlcv:{ticker.upper()}:{period}"
    if not force:
        cached = DATA_CACHE.get(key)
        if cached is not None:
            return cached

    frame = None
    source = "supabase"
    if db.available():
        frame = db.read_ohlcv(ticker.upper(), PERIOD_LOOKBACK.get(period, 180))
        if frame is not None and not _is_fresh(frame):
            frame = None

    if frame is None:
        frame = _download_with_retry(ticker.upper(), period)
        frame = augment(frame)
        source = "yfinance"
        _persist_to_db(ticker.upper(), frame)

    frame.attrs["ticker"] = ticker.upper()
    frame.attrs["period"] = period
    frame.attrs["source"] = source
    DATA_CACHE.set(key, frame)
    DATA_CACHE.set(f"ohlcv:{ticker.upper()}:meta", {"period": period, "points": len(frame), "source": source})
    return frame


def _is_fresh(frame):
    if frame is None or len(frame) == 0:
        return False
    last_date = frame.index[-1]
    if hasattr(last_date, "to_pydatetime"):
        last_date = last_date.to_pydatetime().date()
    return (date.today() - last_date).days <= FRESH_DAYS


def _persist_to_db(ticker, frame):
    try:
        rows = []
        for idx, row in frame.iterrows():
            item = {"date": _to_date(idx)}
            for upper, lower in _COLUMN_MAP.items():
                item[lower] = _clean_value(row[upper])
            rows.append(item)
        db.upsert_ohlcv(ticker, rows)
    except Exception:
        pass


def _download_with_retry(ticker, period, attempts=2):
    last_error = None
    for _ in range(attempts):
        try:
            hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
            if hist is None or hist.empty:
                raise ValueError("Sin datos devueltos por yfinance")
            frame = hist.dropna(subset=["Close"]).copy()
            frame = frame.reset_index()
            for column in ["Open", "High", "Low", "Close", "Volume"]:
                if column not in frame.columns:
                    frame[column] = None
            frame = frame[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
            dates = frame["Date"]
            frame.index = _to_datetime(dates)
            frame.drop(columns=["Date"], inplace=True)
            return frame.tail(PERIOD_LOOKBACK.get(period, 180))
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"No fue posible descargar datos de {ticker}: {last_error}")


def _to_datetime(dates):
    if hasattr(dates, "dt"):
        return pd.to_datetime(dates.dt.tz_localize(None) if getattr(dates.dt, "tz", None) else dates)
    return pd.to_datetime(pd.Series(dates))


def _to_date(value):
    if hasattr(value, "date"):
        return value.date()
    return value


def _clean_value(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def series_payload(frame, limit=180):
    work = frame.tail(limit)
    dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) for d in work.index]
    return {
        "dates": dates,
        "close": _round_list(work["Close"]),
        "open": _round_list(work["Open"]),
        "high": _round_list(work["High"]),
        "low": _round_list(work["Low"]),
        "volume": [_int_volume(v) for v in work["Volume"]],
        "sma20": _round_list(work["SMA20"]),
        "sma50": _round_list(work["SMA50"]),
        "rsi14": _round_list(work["RSI14"]),
        "macd": _round_list(work["MACD"]),
        "macd_signal": _round_list(work["MACD_SIGNAL"]),
        "macd_hist": _round_list(work["MACD_HIST"]),
        "atr14": _round_list(work["ATR14"]),
    }


def _round_list(series):
    result = []
    for value in series:
        if value is None:
            result.append(None)
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            result.append(None)
            continue
        if math.isnan(number) or math.isinf(number):
            result.append(None)
        else:
            result.append(round(number, 6))
    return result


def _int_volume(value):
    try:
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return 0
        return int(number)
    except (TypeError, ValueError):
        return 0