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

DB_PATH = r"C:\Users\preet\OneDrive\Desktop\Aswin\Quant_app\prices.db"

@app.get("/api/history")
def get_history(symbol: str = "RELIANCE"):
    conn = duckdb.connect(DB_PATH)

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

    df = conn.execute(query).df()
    conn.close()

    return df.to_dict(orient="records")

@app.get("/api/symbols")
def get_symbols():
    conn = duckdb.connect(DB_PATH)

    df = conn.execute("""
        SELECT DISTINCT symbol
        FROM prices
        ORDER BY symbol
    """).df()

    conn.close()

    return df["symbol"].tolist()
