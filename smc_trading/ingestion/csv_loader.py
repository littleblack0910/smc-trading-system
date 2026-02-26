from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd


def load_price_csv(
    path: str | Path,
    *,
    date_col: str = "date",
    price_col: str = "close",
    tz: str | None = None,
    ohlc_mode: Literal["close_only", "ohlc"] = "close_only",
) -> pd.DataFrame:
    """Load a simple OHLC/close CSV for backtesting.

    Expected schema (minimum):
    - date: ISO-8601 string
    - close: float

    Optionally, the CSV can also contain: open, high, low, volume.

    This is intentionally lightweight for Week 1 so we can focus on
    the backtest loop and CLI plumbing, not data engineering.
    """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    if date_col not in df.columns:
        raise ValueError(f"CSV is missing required date column: {date_col}")
    if price_col not in df.columns:
        raise ValueError(f"CSV is missing required price column: {price_col}")

    df[date_col] = pd.to_datetime(df[date_col])
    if tz:
        df[date_col] = df[date_col].dt.tz_localize(tz)

    df = df.sort_values(date_col).set_index(date_col)

    if ohlc_mode == "close_only":
        return df[[price_col]].rename(columns={price_col: "close"})

    # For now we just return the frame as-is; later we can normalize
    # column names into a canonical OHLC schema.
    return df
