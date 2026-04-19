import os

DB_PATH = "prices.db"

# Tickers file path — single source of truth
_TICKERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickers.txt")


def load_tickers() -> list[str]:
    """Read tickers from tickers.txt and return as a list (no .NS suffix)."""
    with open(_TICKERS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]


def load_tickers_ns() -> list[str]:
    """Read tickers from tickers.txt and append .NS suffix for yfinance."""
    return [t + ".NS" for t in load_tickers()]

