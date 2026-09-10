COMPANIES = {
    "SPY": {"ticker": "SPY", "name": "S&P 500 ETF"},
    "AAPL": {"ticker": "AAPL", "name": "Apple Inc."},
    "NVDA": {"ticker": "NVDA", "name": "NVIDIA Corp."},
}


def resolve(ticker):
    t = ticker.upper().strip()
    return COMPANIES.get(t, {"ticker": t, "name": t})
