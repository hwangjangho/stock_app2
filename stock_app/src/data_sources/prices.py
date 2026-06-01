from __future__ import annotations

from datetime import datetime, timedelta
import pandas as pd


def _normalize_ticker(country: str, ticker: str) -> str:
    t = (ticker or "").strip()
    c = (country or "").strip().lower()

    if c in ["kr", "korea", "kor", "south korea", "krx"]:
        if t.endswith(".KS") or t.endswith(".KQ"):
            t = t.split(".")[0]

    return t


def get_price_history(country: str, ticker: str, years: int = 2) -> pd.DataFrame:
    import FinanceDataReader as fdr

    ticker = _normalize_ticker(country, ticker)

    end = datetime.today()
    start = end - timedelta(days=365 * years)

    df = fdr.DataReader(ticker, start, end)

    if df is None or df.empty:
        raise ValueError(f"{ticker} 종목의 가격 데이터를 불러오지 못했습니다.")

    df = df.reset_index()
    df = df.rename(columns={"Date": "date", "Close": "close"})

    return df[["date", "close"]]
