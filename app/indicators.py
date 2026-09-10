import numpy as np
import pandas as pd


def sma(series, window):
    return series.rolling(window=window).mean()


def rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    return out.fillna(50.0)


def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def true_range(high, low, close):
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def atr(high, low, close, window=14):
    return true_range(high, low, close).ewm(alpha=1.0 / window, adjust=False).mean()


def augment(df):
    close = df["Close"]
    work = df.copy()
    work["SMA20"] = sma(close, 20)
    work["SMA50"] = sma(close, 50)
    work["RSI14"] = rsi(close, 14)
    macd_line, signal_line, histogram = macd(close)
    work["MACD"] = macd_line
    work["MACD_SIGNAL"] = signal_line
    work["MACD_HIST"] = histogram
    work["ATR14"] = atr(df["High"], df["Low"], close, 14)
    return work


def latest_values(df):
    work = augment(df)
    last = work.iloc[-1]
    previous = work.iloc[-2] if len(work) >= 2 else last
    close_now = float(last["Close"])
    change_pct = (close_now / previous["Close"] - 1.0) * 100.0 if previous["Close"] else 0.0
    return {
        "ticker": str(df.attrs.get("ticker", "")),
        "date": str(last.name.date() if hasattr(last.name, "date") else last.name),
        "close": close_now,
        "change_pct": change_pct,
        "volume": int(last["Volume"]) if "Volume" in last else 0,
        "high": float(last["High"]),
        "low": float(last["Low"]),
        "open": float(last["Open"]),
        "sma20": _clean(last["SMA20"]),
        "sma50": _clean(last["SMA50"]),
        "rsi14": _clean(last["RSI14"]),
        "macd": _clean(last["MACD"]),
        "macd_signal": _clean(last["MACD_SIGNAL"]),
        "macd_hist": _clean(last["MACD_HIST"]),
        "atr14": _clean(last["ATR14"]),
    }


def _clean(value):
    try:
        value = float(value)
        if np.isnan(value) or np.isinf(value):
            return None
        return round(value, 6)
    except (TypeError, ValueError):
        return None