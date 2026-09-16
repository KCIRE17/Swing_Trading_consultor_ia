import argparse
import json
import sys
import urllib.request

from app import db

BASE = "https://swing-trading-consultor-ia.vercel.app"


def request(path, timeout=30):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "smoke-remote/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}")
    if detail and not ok:
        print(f"       {detail}")
    return ok


def main():
    global BASE
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    args = parser.parse_args()
    BASE = args.base.rstrip("/")
    print(f"== SMOKE REMOTO: {BASE} ==")

    ok_all = True

    status, health = request("/api/health")
    ok_all &= check("http: /api/health", status == 200 and health.get("status") == "ok", str(health))

    ok_all &= check("db: conexion a Supabase", db.connected(), "revisa DATABASE_URL en el job")

    for endpoint, extra in [
        ("/api/indicators?ticker=SPY&period=3mo", "series"),
        ("/api/forecast?ticker=SPY&period=3mo", "forecast"),
        ("/api/signal?ticker=SPY&period=3mo", "senal"),
        ("/api/backtest?ticker=SPY", "backtest"),
        ("/api/news?ticker=SPY", "noticias"),
        ("/api/screener?tickers=SPY,AAPL&period=3mo", "companies"),
    ]:
        try:
            status, payload = request(endpoint, timeout=60)
            ok = status == 200 and payload.get(extra) is not None
            ok_all &= check(f"http: {endpoint.split('?')[0]}", ok, json.dumps(payload)[:200])
        except Exception as exc:
            ok_all &= check(f"http: {endpoint.split('?')[0]}", False, repr(exc))

    print("== RESULTADO:", "OK" if ok_all else "CON FALLAS", "==")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()