from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import duckdb

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DAILY_DB = r"C:\Users\preet\OneDrive\Desktop\Aswin\Quant_app\prices.db"
INTRADAY_DB = r"C:\Users\preet\OneDrive\Desktop\Aswin\Quant_app\intraday.db"


@app.get("/api/history")
def get_history(symbol: str = "RELIANCE", tf: str = "D"):

    # =========================
    # DAILY / WEEKLY / MONTHLY
    # =========================
    if tf in ["D", "W", "M"]:

        conn = duckdb.connect(DAILY_DB)

        if tf == "D":
            query = f"""
                SELECT
                    date as time,
                    open,
                    high,
                    low,
                    close
                FROM prices
                WHERE symbol = '{symbol}'
                ORDER BY date
            """

        elif tf == "W":
            query = f"""
                SELECT
                    date_trunc('week', date) as time,
                    first(open) as open,
                    max(high) as high,
                    min(low) as low,
                    last(close) as close
                FROM prices
                WHERE symbol = '{symbol}'
                GROUP BY 1
                ORDER BY 1
            """

        else:   # M
            query = f"""
                SELECT
                    date_trunc('month', date) as time,
                    first(open) as open,
                    max(high) as high,
                    min(low) as low,
                    last(close) as close
                FROM prices
                WHERE symbol = '{symbol}'
                GROUP BY 1
                ORDER BY 1
            """

        df = conn.execute(query).df()
        conn.close()

        return df.to_dict(orient="records")

    # =========================
    # INTRADAY
    # =========================
    else:

        conn = duckdb.connect(INTRADAY_DB)

        if tf == "1m":
            query = f"""
                SELECT
                    datetime as time,
                    open,
                    high,
                    low,
                    close
                FROM prices_intraday
                WHERE symbol = '{symbol}'
                ORDER BY datetime ASC
            """

        elif tf == "5m":
            query = f"""
                SELECT
                    date_trunc('minute', datetime)
                    - INTERVAL (EXTRACT(MINUTE FROM datetime) % 5) MINUTE
                    as time,

                    first(open) as open,
                    max(high) as high,
                    min(low) as low,
                    last(close) as close

                FROM prices_intraday
                WHERE symbol = '{symbol}'
                GROUP BY 1
                ORDER BY 1
            """

        elif tf == "15m":
            query = f"""
                SELECT
                    date_trunc('minute', datetime)
                    - INTERVAL (EXTRACT(MINUTE FROM datetime) % 15) MINUTE
                    as time,

                    first(open) as open,
                    max(high) as high,
                    min(low) as low,
                    last(close) as close

                FROM prices_intraday
                WHERE symbol = '{symbol}'
                GROUP BY 1
                ORDER BY 1
            """

        elif tf == "1H":
            query = f"""
                SELECT
                    date_trunc('hour', datetime) as time,

                    first(open) as open,
                    max(high) as high,
                    min(low) as low,
                    last(close) as close

                FROM prices_intraday
                WHERE symbol = '{symbol}'
                GROUP BY 1
                ORDER BY 1
            """

        else:
            query = f"""
                SELECT
                    datetime as time,
                    open,
                    high,
                    low,
                    close
                FROM prices_intraday
                WHERE symbol = '{symbol}'
                ORDER BY datetime ASC
            """

        df = conn.execute(query).df()
        conn.close()

        return df.to_dict(orient="records")


@app.get("/api/symbols")
def get_symbols():

    conn = duckdb.connect(DAILY_DB)

    df = conn.execute("""
        SELECT DISTINCT symbol
        FROM prices
        ORDER BY symbol
    """).df()

    conn.close()

    return df["symbol"].tolist()
