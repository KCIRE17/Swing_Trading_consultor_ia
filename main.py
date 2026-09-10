import os

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import arima_benchmark, backtest as backtest_engine
from app import gemini_client, signal_engine
from app.cache import DATA_CACHE
from app.data import fetch_ohlcv, series_payload
from app.indicators import latest_values

app = FastAPI(
    title="Swing Trading Consulter IA",
    description="MVP del sistema de soporte a la toma de decisiones para Swing Trading "
    "con Business Analytics e IA multimodal.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_TICKERS = ["SPY", "AAPL", "NVDA", "MSFT"]


class AnalyzeRequest(BaseModel):
    ticker: str
    period: str = "6mo"
    image_url: str | None = None


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "gemini_key_present": bool(os.environ.get("GEMINI_API_KEY")),
    }


@app.get("/api/indicators")
def indicators(ticker: str = Query(..., min_length=1), period: str = "6mo"):
    try:
        frame = fetch_ohlcv(ticker, period)
        return {
            "ticker": ticker.upper(),
            "period": period,
            "ultimo": latest_values(frame),
            "series": series_payload(frame),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


@app.get("/api/forecast")
def forecast(ticker: str = Query(..., min_length=1), period: str = "6mo"):
    try:
        frame = fetch_ohlcv(ticker, period)
        result = arima_benchmark.estimate(frame)
        result["forecast_dates"] = _next_business_days(result.get("last_close"), len(result["forecast"]))
        return {
            "ticker": ticker.upper(),
            "period": period,
            "forecast": result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    try:
        context = _build_context(request.ticker, request.period)
        gemini = gemini_client.analyze(context, request.image_url)
        return {"ticker": request.ticker.upper(), "analisis": gemini}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


@app.get("/api/signal")
def signal(
    ticker: str = Query(..., min_length=1),
    period: str = "6mo",
    image_url: str | None = Query(default=None),
):
    try:
        context = _build_context(ticker, period)
        gemini = gemini_client.analyze(context, image_url)
        decision = signal_engine.decide(context, gemini)
        return {"ticker": ticker.upper(), "contexto_tecnico": context, "analisis_ia": gemini, "senal": decision}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


@app.get("/api/backtest")
def backtest(ticker: str = Query(..., min_length=1), period: str = "1y"):
    try:
        frame = fetch_ohlcv(ticker, period)
        arima = None
        try:
            arima = arima_benchmark.estimate(frame)["forecast"]
        except Exception:
            arima = None
        result = backtest_engine.run(frame, arima)
        return {"ticker": ticker.upper(), "period": period, "backtest": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


@app.get("/api/refresh")
def refresh(tickers: str = Query(default=",".join(DEFAULT_TICKERS))):
    items = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    results = []
    for ticker in items:
        status, payload = "ok", {}
        try:
            frame = fetch_ohlcv(ticker, "6mo", force=True)
            last = latest_values(frame)
            forecast_value = None
            try:
                forecast_value = arima_benchmark.estimate(frame)["next_close"]
            except Exception:
                pass
            payload = {"close": last["close"], "rsi14": last["rsi14"], "forecast_next": forecast_value}
        except Exception as exc:
            status = "error"
            payload = {"error": _message(exc)}
        results.append({"ticker": ticker, "status": status, "datos": payload})
    return {"evento": _cron_origin(), "resultados": results}


def _build_context(ticker, period):
    frame = fetch_ohlcv(ticker, period)
    context = latest_values(frame)
    context["ticker"] = ticker.upper()
    try:
        forecast_result = arima_benchmark.estimate(frame)
        context["arima_forecast"] = forecast_result["forecast"]
        context["arima_next"] = forecast_result["next_close"]
        context["arima_order"] = forecast_result["order"]
        context["arima_adf_pvalue"] = forecast_result["adf_pvalue"]
    except Exception:
        context["arima_forecast"] = None
        context["arima_next"] = None
    return context


def _next_business_days(last_close, n):
    start = pd.Timestamp.today().normalize()
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(start=start, periods=max(n, 5))]


def _message(exc):
    detail = str(exc)
    if len(detail) > 400:
        detail = detail[:400]
    return {"error": True, "mensaje": detail}


def _cron_origin():
    return "vercel-cron" if os.environ.get("VERCEL") else "manual"


if not os.environ.get("VERCEL"):
    from pathlib import Path

    from fastapi.staticfiles import StaticFiles

    _public = Path(__file__).resolve().parent / "public"
    if _public.exists():
        app.mount("/", StaticFiles(directory=str(_public), html=True), name="static")