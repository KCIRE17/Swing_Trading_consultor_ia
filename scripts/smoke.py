import sys
import time

from app import arima_benchmark, backtest as backtest_engine
from app import gemini_client, signal_engine
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
    context = {"ticker": "SPY", "close": 200, "sma20": 198, "sma50": 195, "rsi14": 55, "macd": 1.0, "macd_signal": 0.5}
    result = gemini_client.analyze(context, image_url=None)
    ok = result["prediccion"] == "NEUTRAL" and result["probabilidad"] == 0.5
    check("gemini: degrada sin GEMINI_API_KEY", ok, str(result))

    decision = signal_engine.decide(context, result)
    check("señal: decide HOLD en degradado", decision["direccion"] == "HOLD", str(decision))


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
        check("http: /api/health", response.status_code == 200, response.text)

        start = time.time()
        payload = client.get("/api/indicators?ticker=SPY&period=3mo")
        ok = payload.status_code == 200 and payload.json().get("series") and len(payload.json()["series"]["dates"]) > 0
        check("http: /api/indicators (serializable sin NaN)", ok, payload.text[:300], start=start)

        resp_forecast = client.get("/api/forecast?ticker=SPY&period=3mo")
        check("http: /api/forecast", resp_forecast.status_code == 200, resp_forecast.text[:200])

        resp_signal = client.get("/api/signal?ticker=SPY&period=3mo")
        ok_signal = resp_signal.status_code == 200 and resp_signal.json().get("senal", {}).get("direccion") in ("BUY", "HOLD", "SELL")
        check("http: /api/signal (degradado sin gemini)", ok_signal, resp_signal.text[:200])

        resp_bt = client.get("/api/backtest?ticker=SPY")
        check("http: /api/backtest", resp_bt.status_code == 200, resp_bt.text[:200])

        resp_fav = client.get("/favicon.ico")
        check("http: /favicon.ico", resp_fav.status_code == 200, resp_fav.text[:80])
    except Exception as exc:
        check("http: endpoints", False, repr(exc))

    print("== FIN ==")


if __name__ == "__main__":
    main()