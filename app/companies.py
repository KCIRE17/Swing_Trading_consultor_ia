COMPANIES = {
    "NVDA": {"ticker": "NVDA", "name": "NVIDIA Corporation"},
    "AAPL": {"ticker": "AAPL", "name": "Apple Inc."},
    "MSFT": {"ticker": "MSFT", "name": "Microsoft Corporation"},
}

SCREENER_TICKERS = ["NVDA", "AAPL", "MSFT"]


def resolve(ticker):
    t = ticker.upper().strip()
    return COMPANIES.get(t, {"ticker": t, "name": t})
