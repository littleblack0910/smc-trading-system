from pathlib import Path

import pandas as pd
import pytest

from smc_trading.ingestion.csv_loader import load_price_csv


def test_load_price_csv_happy_path(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text(
        """date,close,open,high,low,volume
2024-01-01,100,99,101,98,1000000
2024-01-02,102,101,103,100,1200000
""",
        encoding="utf-8",
    )

    df = load_price_csv(csv_path)

    assert list(df.columns) == ["close"]
    assert df.index.name == "date"
    assert len(df) == 2
    assert df["close"].iloc[0] == 100


def test_load_price_csv_missing_date_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("price,close\n100,100\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_price_csv(csv_path)


def test_load_price_csv_missing_close_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("date,price\n2024-01-01,100\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_price_csv(csv_path)


def test_load_price_csv_with_timezone(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("date,close\n2024-01-01,100\n", encoding="utf-8")

    df = load_price_csv(csv_path, tz="America/New_York")

    assert isinstance(df.index[0], pd.Timestamp)
    assert df.index.tz is not None
