import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

HORIZON = 5
P_GRID = [0, 1, 2]
Q_GRID = [0, 1, 2]


def estimate(frame):
    close = frame["Close"].dropna().astype(float)
    if len(close) < 30:
        raise ValueError("Serie de precios demasiado corta para ARIMA")

    differencing, adf_pvalue = _find_stationary_order(close)
    try:
        best_order, best_aic, model_fit = _fit_best(close.to_numpy(), differencing)
        forecast_values = [float(v) for v in model_fit.forecast(HORIZON)]
        method = "arima"
    except Exception:
        forecast_values, best_order, best_aic = _trend_fallback(close)
        method = "trend"

    last_close = float(close.iloc[-1])
    next_close = float(forecast_values[-1])
    return {
        "adf_pvalue": round(adf_pvalue, 6),
        "d": differencing,
        "order": {"p": best_order[0], "d": best_order[1], "q": best_order[2]},
        "aic": round(best_aic, 4) if best_aic is not None else None,
        "forecast": [_round(v) for v in forecast_values],
        "forecast_dates": [],
        "last_close": round(last_close, 4),
        "next_close": round(next_close, 4),
        "method": method,
        "points": len(close),
    }


def _find_stationary_order(series):
    current = series
    for d in range(3):
        pvalue = float(adfuller(current)[1])
        if pvalue <= 0.05:
            return d, pvalue
        current = current.diff().dropna()
    return 2, float(adfuller(current)[1])


def _fit_best(close_values, d):
    candidates = [(p, d, q) for p in P_GRID for q in Q_GRID if not (p == 0 and q == 0)]
    best_order = None
    best_aic = None
    best_fit = None
    for order in candidates:
        try:
            fit = ARIMA(close_values, order=order).fit()
            aic = float(fit.aic)
            if best_aic is None or aic < best_aic:
                best_order, best_aic, best_fit = order, aic, fit
        except Exception:
            continue
    if best_fit is None:
        raise ValueError("No fue posible calibtrar un modelo ARIMA")
    return best_order, best_aic, best_fit


def _trend_fallback(close):
    values = close.to_numpy()[-20:].astype(float)
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    forecast_values = [intercept + slope * (len(values) + h) for h in range(1, HORIZON + 1)]
    return forecast_values, (1, 1, 0), None


def _round(value):
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None