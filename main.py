import os

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app import advisor, arima_benchmark, backtest as backtest_engine
from app import companies, db, gemini_client, narrator, signal_engine
from app.cache import DATA_CACHE
from app.data import fetch_ohlcv, series_payload
from app.indicators import latest_values

app = FastAPI(
    title="Swing Trading Consulter IA",
    description="Sistema de soporte a la toma de decisiones para Swing Trading con "
    "Business Analytics, IA cualitativa y Machine Learning clásico (3 vistas).",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_TICKERS = ["SPY", "AAPL", "NVDA", "MSFT"]


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "base_de_datos": db.connected() if db.available() else False,
        "sentimiento_modelo": _sentiment_available(),
        "gemini_key_present": bool(os.environ.get("GEMINI_API_KEY")),
    }


def _sentiment_available():
    from app import sentiment

    return sentiment.available()


@app.get("/api/indicators")
def indicators(ticker: str = Query(..., min_length=1), period: str = "6mo"):
    try:
        frame = fetch_ohlcv(ticker, period)
        company = companies.resolve(ticker)
        ultimo = latest_values(frame)
        return {
            "ticker": company["ticker"],
            "nombre": company["name"],
            "period": period,
            "ultimo": ultimo,
            "series": series_payload(frame),
            "meta": _data_meta(ticker, period, frame),
            "asesoria": {
                "precio": advisor.describe_precio(
                    ultimo.get("close"), ultimo.get("sma20"), ultimo.get("sma50"), ultimo.get("change_pct")
                ),
                "rsi": advisor.describe_rsi(ultimo.get("rsi14")),
                "macd": advisor.describe_macd(
                    ultimo.get("macd"), ultimo.get("macd_signal"), ultimo.get("macd_hist")
                ),
                "decision": advisor.resumen_descriptiva(
                    ultimo.get("close"),
                    ultimo.get("sma20"),
                    ultimo.get("sma50"),
                    ultimo.get("rsi14"),
                    ultimo.get("macd"),
                    ultimo.get("macd_signal"),
                    ultimo.get("macd_hist"),
                    ultimo.get("atr14"),
                    ultimo.get("change_pct"),
                ),
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


@app.get("/api/forecast")
def forecast(ticker: str = Query(..., min_length=1), period: str = "6mo"):
    try:
        result = _forecast_snapshot(ticker.upper(), period)
        result["asesoria"] = advisor.advise_arima(
            result.get("next_close"),
            result.get("last_close"),
            result.get("order"),
            result.get("adf_pvalue"),
        )
        return {
            "ticker": ticker.upper(),
            "period": period,
            "forecast": result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


def _forecast_snapshot(ticker, period):
    frame = fetch_ohlcv(ticker, period)
    last_close = latest_values(frame).get("close")
    snapshot = None
    if db.available():
        try:
            snapshot = db.read_latest_forecast(ticker)
        except Exception:
            snapshot = None
    if snapshot is not None and snapshot.get("forecast"):
        order = snapshot.get("order") or {}
        result = {
            "adf_pvalue": None,
            "d": order.get("d"),
            "order": order,
            "aic": snapshot.get("aic"),
            "forecast": [float(v) for v in snapshot["forecast"]],
            "forecast_dates": [],
            "last_close": round(last_close, 4) if last_close is not None else None,
            "next_close": (
                round(float(snapshot.get("next_close")), 4) if snapshot.get("next_close") is not None else None
            ),
            "method": snapshot.get("method", "arima"),
            "points": int(len(frame)),
            "fecha_generado": str(snapshot.get("fecha_generado")) if snapshot.get("fecha_generado") else None,
            "fuente": "supabase",
        }
    else:
        result = arima_benchmark.estimate(frame)
        result["fuente"] = "en_vivo"
    result["forecast_dates"] = _next_business_days(result.get("last_close"), len(result.get("forecast") or []))
    return result


@app.get("/api/signal")
def signal(
    ticker: str = Query(..., min_length=1),
    period: str = "6mo",
):
    return _build_signal_response(ticker, period)


def _build_signal_response(ticker, period):
    try:
        context = _build_context(ticker, period)
        gemini = gemini_client.analyze(context)
        decision = signal_engine.decide(context, gemini)
        company = companies.resolve(ticker)
        narracion = narrator.explain(context, decision)
        enriched = gemini_client.enrich_narrative(narracion["parrafo"], context)
        if enriched:
            narracion = {"parrafo": enriched, "bullets": narracion["bullets"], "fuente": "gemini"}
        noticias = context.get("noticias") or {}
        decision_predictiva = advisor.resumen_predictiva(
            context.get("arima_next"),
            context.get("close"),
            gemini.get("prediccion"),
            gemini.get("probabilidad"),
            gemini.get("nivel_riesgo"),
            noticias,
        )
        return {
            "ticker": company["ticker"],
            "nombre": company["name"],
            "contexto_tecnico": context,
            "analisis_ia": gemini,
            "senal": decision,
            "narracion": narracion,
            "decision_predictiva": decision_predictiva,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


@app.get("/api/news")
def news(ticker: str = Query(..., min_length=1), limit: int = Query(default=12)):
    try:
        items = db.read_news(ticker.upper(), limit) if db.available() else []
        noticias = [
            {
                "titulo": row.get("titulo"),
                "url": row.get("url"),
                "publisher": row.get("publisher"),
                "fecha": _iso(row.get("fecha")),
                "fecha_extraido": str(row.get("fecha_extraido")),
                "sentimiento": row.get("sentimiento"),
                "prob_pos": row.get("prob_pos"),
                "prob_neu": row.get("prob_neu"),
                "prob_neg": row.get("prob_neg"),
            }
            for row in items
        ]
        return {"ticker": ticker.upper(), "noticias": noticias}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=_message(exc))


def _iso(value):
    if not value:
        return None
    return str(value)[:19]


@app.get("/api/interpret")
def interpret(ticker: str = Query(..., min_length=1), period: str = "6mo"):
    try:
        context = _build_context(ticker, period)
        gemini = gemini_client.analyze(context)
        decision = signal_engine.decide(context, gemini)
        company = companies.resolve(ticker)
        narracion = narrator.explain(context, decision)
        enriched = gemini_client.enrich_narrative(narracion["parrafo"], context)
        if enriched:
            narracion = {"parrafo": enriched, "bullets": narracion["bullets"], "fuente": "gemini"}
        return {
            "ticker": company["ticker"],
            "nombre": company["name"],
            "narracion": narracion,
        }
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
        result["asesoria"] = advisor.advise_backtest(result)
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


@app.get("/api/screener")
def screener(
    tickers: str = Query(default=",".join(companies.SCREENER_TICKERS)),
    period: str = "6mo",
):
    items = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    companies_list = []
    for ticker in items:
        row = {"ticker": ticker, "error": None}
        try:
            frame = fetch_ohlcv(ticker, period)
            company = companies.resolve(ticker)
            ultimo = latest_values(frame)
            row.update(
                {
                    "nombre": company["name"],
                    "close": ultimo["close"],
                    "change_pct": ultimo["change_pct"],
                    "volume": ultimo["volume"],
                    "rsi14": ultimo["rsi14"],
                    "macd_hist": ultimo["macd_hist"],
                    "atr14": ultimo["atr14"],
                    "sma20": ultimo["sma20"],
                    "sma50": ultimo["sma50"],
                    "ultima_fecha": ultimo["date"],
                    "senal": advisor.advise_screener(
                        ultimo["close"], ultimo["sma20"], ultimo["sma50"], ultimo["rsi14"], ultimo["macd_hist"]
                    ),
                    "asesoria": advisor.advise_precio(
                        ultimo["close"], ultimo["sma20"], ultimo["sma50"], ultimo["change_pct"]
                    ),
                }
            )
        except Exception as exc:
            row["error"] = _message(exc)
        companies_list.append(row)
    return {"period": period, "companies": companies_list}


def _data_meta(ticker, period, frame):
    last_date = None
    try:
        last_date = str(frame.index[-1].date())
    except Exception:
        pass
    source = frame.attrs.get("source", "supabase")
    return {
        "proveedor": "Supabase Postgres" if source == "supabase" else "Yahoo Finance (recarga en vivo)",
        "tipo": "OHLCV historico + indicadores",
        "period_solicitado": period,
        "n_velas": int(len(frame)),
        "ultima_fecha": last_date,
    }


def _build_context(ticker, period):
    frame = fetch_ohlcv(ticker, period)
    context = latest_values(frame)
    context["ticker"] = ticker.upper()
    context["noticias"] = _news_summary(ticker.upper())
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


def _news_summary(ticker):
    counts = {"POS": 0, "NEU": 0, "NEG": 0}
    if db.available():
        try:
            for row in db.read_news(ticker, 15):
                code = row.get("sentimiento")
                if code in counts:
                    counts[code] += 1
        except Exception:
            pass
    total = sum(counts.values())
    return {
        "total": total,
        "counts": counts,
        "pos_ratio": round(counts["POS"] / total, 4) if total else None,
        "neg_ratio": round(counts["NEG"] / total, 4) if total else None,
    }


def _next_business_days(last_close, n):
    start = pd.Timestamp.today().normalize()
    return [d.strftime("%Y-%m-%d") for d in pd.bdate_range(start=start, periods=max(n, 5))]


def _message(exc):
    detail = str(exc)
    if len(detail) > 400:
        detail = detail[:400]
    return {"error": True, "mensaje": detail}


def _cron_origin():
    return "manual"


_FAVICON_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    b'<text y=".9em" font-size="90">&#x1F4C8;</text></svg>'
)


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
def favicon():
    return Response(content=_FAVICON_SVG, media_type="image/svg+xml")


if not os.environ.get("VERCEL"):
    from pathlib import Path

    from fastapi.staticfiles import StaticFiles

    _public = Path(__file__).resolve().parent / "public"
    if _public.exists():
        app.mount("/", StaticFiles(directory=str(_public), html=True), name="static")