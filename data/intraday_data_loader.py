import duckdb
import pandas as pd
import datetime
import time

from kiteconnect import KiteConnect
from utils import load_tickers

# ==================================================
# CONFIG
# ==================================================
DB_PATH = "intraday.db"
TABLE_NAME = "prices_intraday"
INTERVAL = "minute"          # minute / 5minute / 15minute etc

API_KEY = "74rj48jkshla0dgo"
ACCESS_TOKEN = "JQBtxRrPYLHobjTSFDUU4chcLH8nBVJj"

# ==================================================
# KITE SETUP
# ==================================================
kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# ==================================================
# HELPERS
# ==================================================
def is_weekday(dt: datetime.datetime) -> bool:
    return dt.weekday() < 5


def market_close_now() -> datetime.datetime:
    """
    Use current time.
    If weekend, roll back to Friday 15:30.
    """
    now = datetime.datetime.now()

    while not is_weekday(now):
        now -= datetime.timedelta(days=1)

    return now


def get_start_datetime(con, symbol: str) -> datetime.datetime:
    """
    Get latest candle from DB.
    If none, start 60 days back.
    """
    last_dt = con.execute(f"""
        SELECT MAX(datetime)
        FROM {TABLE_NAME}
        WHERE symbol = ?
    """, [symbol]).fetchone()[0]

    if last_dt is None:
        return datetime.datetime.now() - datetime.timedelta(days=60)

    return last_dt + datetime.timedelta(minutes=1)


# ==================================================
# CONNECT DB
# ==================================================
con = duckdb.connect(DB_PATH)

# ==================================================
# CREATE TABLE IF NOT EXISTS
# ==================================================
con.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    symbol VARCHAR,
    datetime TIMESTAMP,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    PRIMARY KEY(symbol, datetime)
)
""")

# Optional index for faster reads
con.execute(f"""
CREATE INDEX IF NOT EXISTS idx_symbol_datetime
ON {TABLE_NAME}(symbol, datetime)
""")

try:
    # ==================================================
    # LOAD SYMBOLS
    # ==================================================
    symbols = load_tickers()
    print(f"Tickers loaded: {len(symbols)}")

    # ==================================================
    # LOAD INSTRUMENTS
    # ==================================================
    print("Downloading NSE instrument list...")

    instruments = kite.instruments("NSE")
    inst_df = pd.DataFrame(instruments)

    token_map = {
        row["tradingsymbol"]: row["instrument_token"]
        for _, row in inst_df.iterrows()
    }

    # ==================================================
    # FETCH FUNCTION
    # ==================================================
    def fetch_intraday(symbol: str) -> pd.DataFrame:

        token = token_map.get(symbol)

        if not token:
            print(f"Skipping {symbol} (token not found)")
            return pd.DataFrame()

        start_dt = get_start_datetime(con, symbol)
        end_dt = market_close_now()

        while not is_weekday(start_dt):
            start_dt += datetime.timedelta(days=1)

        if start_dt >= end_dt:
            return pd.DataFrame()

        print(f"{symbol}: {start_dt} -> {end_dt}")

        all_rows = []
        current = start_dt

        while current < end_dt:

            next_dt = min(
                current + datetime.timedelta(days=30),
                end_dt
            )

            try:
                data = kite.historical_data(
                    instrument_token=token,
                    from_date=current,
                    to_date=next_dt,
                    interval=INTERVAL
                )

                for row in data:
                    row["symbol"] = symbol

                all_rows.extend(data)

            except Exception as e:
                print(f"{symbol} chunk error: {e}")

            current = next_dt
            time.sleep(0.35)   # rate-limit kindness

        if not all_rows:
            return pd.DataFrame()

        df = pd.DataFrame(all_rows)

        df.rename(columns={"date": "datetime"}, inplace=True)

        df = df[
            ["symbol", "datetime", "open", "high", "low", "close", "volume"]
        ]

        # Remove weekends just in case
        df = df[df["datetime"].dt.weekday < 5]

        return df

    # ==================================================
    # LOOP SYMBOLS
    # ==================================================
    frames = []

    for symbol in symbols:

        try:
            df = fetch_intraday(symbol)

            if not df.empty:
                frames.append(df)

        except Exception as e:
            print(f"{symbol} failed: {e}")

        time.sleep(0.20)

    # ==================================================
    # INSERT
    # ==================================================
    if not frames:
        print("No new intraday data.")
        raise SystemExit(0)

    intraday_df = pd.concat(frames, ignore_index=True)

    con.execute(f"""
        INSERT INTO {TABLE_NAME}
        SELECT *
        FROM intraday_df
        ON CONFLICT(symbol, datetime) DO NOTHING
    """)

    print(f"\nInserted rows: {len(intraday_df)}")

    # ==================================================
    # SANITY CHECK
    # ==================================================
    print(
        con.execute(f"""
        SELECT
            symbol,
            COUNT(*) AS rows,
            MIN(datetime) AS start_dt,
            MAX(datetime) AS end_dt
        FROM {TABLE_NAME}
        GROUP BY symbol
        ORDER BY symbol
        """).fetchdf()
    )

finally:
    con.close()
