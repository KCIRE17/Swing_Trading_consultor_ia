COMPANIES = {
    "SPY": {"ticker": "SPY", "name": "S&P 500 ETF Trust (SPDR)"},
    "AAPL": {"ticker": "AAPL", "name": "Apple Inc."},
    "NVDA": {"ticker": "NVDA", "name": "NVIDIA Corporation"},
    "MSFT": {"ticker": "MSFT", "name": "Microsoft Corporation"},
    "AMZN": {"ticker": "AMZN", "name": "Amazon.com, Inc."},
    "TSLA": {"ticker": "TSLA", "name": "Tesla, Inc."},
    "GOOGL": {"ticker": "GOOGL", "name": "Google"},
    "META": {"ticker": "META", "name": "Meta Platforms, Inc."},
}

SCREENER_TICKERS = ["SPY", "AAPL", "NVDA", "MSFT", "AMZN", "TSLA", "GOOGL", "META"]


def resolve(ticker):
    t = ticker.upper().strip()
    return COMPANIES.get(t, {"ticker": t, "name": t})
