import sys
import time

from app import advisor, arima_benchmark, backtest as backtest_engine
from app import companies, db, gemini_client, narrator, sentiment, signal_engine
from app.data import fetch_ohlcv, series_payload
from app.indicators import latest_values


def check(name, ok, detail="", start=None):
    elapsed = f" ({time.time() - start:.1f}s)" if start else ""
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}{elapsed}")
    if detail and not ok:
        print(f"       {detail}")
    return ok


def run_ticker(ticker, period="6mo"):
    start = time.time()
    frame = fetch_ohlcv(ticker, period, force=True)
    check(f"{ticker}: fetch_ohlcv [{len(frame)} velas]", len(frame) >= 50, start=start)

    latest = latest_values(frame)
    check(
        f"{ticker}: indicadores (rsi/macd/atr/sma)",
        all(v is not None for v in [latest["rsi14"], latest["macd"], latest["atr14"], latest["sma20"]]),
        str(latest),
    )

    series = series_payload(frame)
    check(f"{ticker}: series_para_graficos", len(series["dates"]) == len(series["close"]) > 0)

    try:
        result = arima_benchmark.estimate(frame)
        ok = len(result["forecast"]) >= 1 and result["next_close"] is not None
        check(f"{ticker}: ARIMA order={result['order']} aic={result['aic']}", ok, str(result))
    except Exception as exc:
        check(f"{ticker}: ARIMA", False, repr(exc))


def run_no_key_degrade():
    context = {
        "ticker": "SPY",
        "close": 200,
        "sma20": 198,
        "sma50": 195,
        "rsi14": 55,
        "macd": 1.0,
        "macd_signal": 0.5,
        "noticias": {"total": 0, "counts": {"POS": 0, "NEU": 0, "NEG": 0}},
    }
    result = gemini_client.analyze(context)
    ok = (
        result["prediccion"] == "NEUTRAL"
        and result["probabilidad"] == 0.5
        and result["recomendacion"] == "MANTENER"
        and bool(result.get("conclusion_cualitativa"))
    )
    check("gemini: degrada sin GEMINI_API_KEY (recomendacion=MANTENER)", ok, str(result))

    decision = signal_engine.decide(context, result)
    check("señal: RETIRAR->SELL / AUMENTAR->BUY / MANTENER->HOLD",
          decision["direccion"] == "HOLD"
          and signal_engine.RECOMENDACION_TO_SEÑAL["AUMENTAR"] == "BUY"
          and signal_engine.RECOMENDACION_TO_SEÑAL["RETIRAR"] == "SELL",
          str(decision))

    movil = narrator.explain(context, decision)
    check("narrador: genera parrafo en espanol", bool(movil["parrafo"] and movil["bullets"]), movil["parrafo"][:160])

    compania = companies.resolve("AAPL")
    check("empresas: nombre real de AAPL", compania["name"] == "Apple Inc.", str(compania))

    if sentiment.available():
        labels = sentiment.classify_texts(["Company reports record profits and raises guidance", "Stock plunges after profit warning"])
        ok_sent = [r["sentimiento"] for r in labels] == ["POS", "NEG"]
        check("sentimiento: ML clasifica POS/NEG", ok_sent, str(labels))
    else:
        check("sentimiento: modelo disponible", False, "corre scripts/train_sentiment.py")


def run_backtest(ticker="SPY"):
    start = time.time()
    frame = fetch_ohlcv(ticker, "1y")
    arima = None
    try:
        arima = arima_benchmark.estimate(frame)["forecast"]
    except Exception:
        pass
    result = backtest_engine.run(frame, arima)
    ok = result.get("disponible") is True or result.get("mensaje")
    check(f"{ticker}: backtest (trades={result.get('n_trades')}, wr={result.get('win_rate')}, dd={result.get('max_drawdown_pct')}%)", ok, start=start)


def main():
    print("== SMOKE TEST: Swing Trading Consulter IA ==")

    start = time.time()
    atxt = advisor.advise_rsi(78)
    check("advisor: RSI sobrecompra -> no invertir", atxt["recomendacion"] == "No invertir", str(atxt), start=start)
    check("companies: nombres completos (AMZN, TSLA, GOOGL, META)",
          all(k in companies.COMPANIES for k in ["AMZN", "TSLA", "GOOGL", "META"]))

    if db.available():
        try:
            db.init_schema()
            check("db: conexion y esquema Supabase", db.connected())
        except Exception as exc:
            check("db: conexion y esquema Supabase", False, repr(exc))
    else:
        check("db: DATABASE_URL (Sin base local)", False, "no configurada; el fallback usa yfinance en vivo")

    for ticker in ["SPY", "AAPL", "NVDA"]:
        try:
            run_ticker(ticker)
        except Exception as exc:
            check(f"{ticker}: pipeline", False, repr(exc))
    run_no_key_degrade()
    try:
        run_backtest("SPY")
    except Exception as exc:
        check("backtest SPY", False, repr(exc))

    try:
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/health")
        check("http: /api/health", response.status_code == 200 and response.json().get("base_de_datos") is not None,
              response.text)

        start = time.time()
        payload = client.get("/api/indicators?ticker=SPY&period=3mo")
        ok = payload.status_code == 200 and payload.json().get("series") and len(payload.json()["series"]["dates"]) > 0
        check("http: /api/indicators (serializable sin NaN)", ok, payload.text[:300], start=start)

        resp_forecast = client.get("/api/forecast?ticker=SPY&period=3mo")
        ok_f = (resp_forecast.status_code == 200
                and resp_forecast.json().get("forecast", {}).get("fuente") in ("supabase", "en_vivo"))
        check("http: /api/forecast", ok_f, resp_forecast.text[:200])

        resp_signal = client.get("/api/signal?ticker=SPY&period=3mo")
        ok_signal = (
            resp_signal.status_code == 200
            and resp_signal.json().get("senal", {}).get("direccion") in ("BUY", "HOLD", "SELL")
            and resp_signal.json().get("senal", {}).get("recomendacion_ia") in ("AUMENTAR", "RETIRAR", "MANTENER")
            and resp_signal.json().get("narracion", {}).get("parrafo")
            and resp_signal.json().get("nombre")
        )
        check("http: /api/signal (degradado + narracion + nombre)", ok_signal, resp_signal.text[:200])

        resp_news = client.get("/api/news?ticker=SPY")
        check("http: /api/news", resp_news.status_code == 200 and "noticias" in resp_news.json(), resp_news.text[:200])

        resp_bt = client.get("/api/backtest?ticker=SPY")
        check("http: /api/backtest", resp_bt.status_code == 200, resp_bt.text[:200])

        resp_sc = client.get("/api/screener?tickers=SPY,AAPL&period=3mo")
        ok_sc = resp_sc.status_code == 200 and len(resp_sc.json().get("companies", [])) == 2 and all(
            c.get("nombre") and c.get("senal") in ("BUY", "HOLD", "SELL") for c in resp_sc.json()["companies"]
        )
        check("http: /api/screener (nombres + senal)", ok_sc, resp_sc.text[:300])

        resp_ind = client.get("/api/indicators?ticker=SPY&period=3mo")
        ok_ind = resp_ind.status_code == 200 and set(resp_ind.json().get("asesoria", {})) >= {"precio", "rsi", "macd"}
        check("http: /api/indicators + asesoria", ok_ind, resp_ind.text[:300], start=time.time())

        resp_arima = client.get("/api/forecast?ticker=SPY&period=3mo")
        ok_arima = resp_arima.status_code == 200 and resp_arima.json().get("forecast", {}).get("asesoria", {}).get("recomendacion")
        check("http: /api/forecast + asesoria", ok_arima, resp_arima.text[:200])

        resp_int = client.get("/api/interpret?ticker=AAPL&period=3mo")
        ok_int = resp_int.status_code == 200 and resp_int.json().get("narracion", {}).get("parrafo")
        check("http: /api/interpret", ok_int, resp_int.text[:200])

        resp_fav = client.get("/favicon.ico")
        check("http: /favicon.ico", resp_fav.status_code == 200, resp_fav.text[:80])
    except Exception as exc:
        check("http: endpoints", False, repr(exc))

    print("== FIN ==")


if __name__ == "__main__":
    main()