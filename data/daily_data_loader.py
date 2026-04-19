import duckdb
import pandas as pd
import datetime
import time

from kiteconnect import KiteConnect
from utils import DB_PATH, load_tickers

# ==================================================
# CONFIG
# ==================================================
TABLE_NAME = "prices"

# First run seed history
SEED_START = datetime.datetime(2018, 1, 1)
SEED_END   = datetime.datetime(2022, 12, 31)

# Zerodha credentials
API_KEY = "74rj48jkshla0dgo"
ACCESS_TOKEN = "JQBtxRrPYLHobjTSFDUU4chcLH8nBVJj"

# API safety
REQUEST_SLEEP = 0.25          # seconds between symbols
CHUNK_DAYS = 1900            # under 2000 day Kite limit

# ==================================================
# KITE LOGIN
# ==================================================
kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# ==================================================
# DB CONNECT
# ==================================================
con = duckdb.connect(DB_PATH)

try:
    # ==================================================
    # FAIL SAFE TABLE CREATION
    # ==================================================
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            symbol VARCHAR,
            date DATE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            PRIMARY KEY(symbol, date)
        )
    """)

    print("Table checked / created.")

    # ==================================================
    # CHECK LAST DATE
    # ==================================================
    latest_date = con.execute(f"""
        SELECT MAX(date) FROM {TABLE_NAME}
    """).fetchone()[0]

    if latest_date is None:
        # ----------------------------------------------
        # FIRST RUN
        # ----------------------------------------------
        start_date = SEED_START
        end_date = SEED_END
        print("First run detected.")
        print(f"Loading seed data: {start_date.date()} to {end_date.date()}")

    else:
        # ----------------------------------------------
        # UPDATE RUN
        # ----------------------------------------------
        start_date = latest_date + datetime.timedelta(days=1)
        end_date = datetime.datetime.today()

        print(f"Database last date: {latest_date}")
        print(f"Updating from {start_date.date()} to {end_date.date()}")

        if start_date > end_date:
            print("Database already up to date.")
            raise SystemExit(0)

    # ==================================================
    # LOAD SYMBOLS
    # ==================================================
    symbols = load_tickers()
    print(f"Tickers loaded: {len(symbols)}")

    # ==================================================
    # LOAD INSTRUMENT TOKENS
    # ==================================================
    print("Fetching instrument master...")

    instruments = kite.instruments("NSE")
    inst_df = pd.DataFrame(instruments)

    token_map = {
        row["tradingsymbol"]: row["instrument_token"]
        for _, row in inst_df.iterrows()
    }

    # ==================================================
    # FETCH FUNCTION
    # ==================================================
    def fetch_symbol(symbol):
        token = token_map.get(symbol)

        if not token:
            print(f"Skipping {symbol}: token missing")
            return pd.DataFrame()

        all_data = []
        current = start_date

        while current <= end_date:

            chunk_end = min(
                current + datetime.timedelta(days=CHUNK_DAYS),
                end_date
            )

            try:
                data = kite.historical_data(
                    token,
                    from_date=current,
                    to_date=chunk_end,
                    interval="day"
                )

                all_data.extend(data)

            except Exception as e:
                print(f"Failed {symbol}: {e}")
                return pd.DataFrame()

            current = chunk_end + datetime.timedelta(days=1)

        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        df["symbol"] = symbol

        return df[
            ["symbol", "date", "open", "high", "low", "close", "volume"]
        ]

    # ==================================================
    # DOWNLOAD LOOP
    # ==================================================
    frames = []

    for i, symbol in enumerate(symbols, start=1):
        print(f"[{i}/{len(symbols)}] {symbol}")

        df = fetch_symbol(symbol)

        if not df.empty:
            frames.append(df)

        time.sleep(REQUEST_SLEEP)

    if not frames:
        print("No new data fetched.")
        raise SystemExit(0)

    prices_df = pd.concat(frames, ignore_index=True)

    # ==================================================
    # INSERT
    # ==================================================
    con.execute(f"""
        INSERT INTO {TABLE_NAME}
        SELECT * FROM prices_df
        ON CONFLICT(symbol, date) DO NOTHING
    """)

    print(f"\nInserted {len(prices_df)} rows.")

    # ==================================================
    # SANITY CHECK
    # ==================================================
    print(
        con.execute(f"""
        SELECT
            symbol,
            COUNT(*) AS rows,
            MIN(date) AS start_date,
            MAX(date) AS end_date
        FROM {TABLE_NAME}
        GROUP BY symbol
        ORDER BY symbol
        """).fetchdf()
    )

finally:
    con.close()
