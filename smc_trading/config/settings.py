from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class BacktestConfig:
    """Configuration for a simple local CSV-based backtest.

    This is intentionally minimal for Week 1: it gives us a typed
    representation of the core knobs we care about while we iterate
    on the broader system design.
    """

    ticker: str
    csv_path: Path
    initial_cash: float = 10_000.0
    # Optional time window; if omitted we use the full CSV.
    start_date: Optional[str] = None  # ISO date (YYYY-MM-DD)
    end_date: Optional[str] = None
    output_path: Optional[Path] = None


def backtest_config_from_args(args: object) -> BacktestConfig:
    """Build a BacktestConfig from an argparse.Namespace-like object.

    Keeping this in a separate function makes it easier to unit-test
    and reuse later when we move from CLI args to config files.
    """

    csv_path = Path(getattr(args, "csv_path"))
    raw_output_path = getattr(args, "output_path", None)
    output_path = Path(raw_output_path) if raw_output_path is not None else None
    return BacktestConfig(
        ticker=getattr(args, "ticker"),
        csv_path=csv_path,
        initial_cash=float(getattr(args, "initial_cash", 10_000.0)),
        start_date=getattr(args, "start_date", None),
        end_date=getattr(args, "end_date", None),
        output_path=output_path,
    )
