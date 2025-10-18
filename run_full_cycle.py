#!/usr/bin/env python3
"""
Utility script for GitHub Actions / cron runs.

Steps:
1. Fetch fresh market data for all configured symbols.
2. Generate AI signals + logs (predictions + analytics).
3. Run backtest and emit summary plus calibrated thresholds.
"""
from __future__ import annotations

import argparse
import sys
from copy import deepcopy
from pathlib import Path
from typing import Iterable, List, Tuple

# Ensure project root is importable even when executed from other directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

from backtest import run_summary  # type: ignore
from data_lake import DataLakePaths  # type: ignore
from prover import (  # type: ignore
    BARS_PER_TF,
    SYMBOLS,
    TIMEFRAMES,
    ai_trade_signal,
    extract_symbol,
    multi_tf_consensus,
)
from signal_logger import log_entry_gap, log_signal  # type: ignore


def _iter_symbols(symbols: Iterable[str]) -> Iterable[str]:
    seen = set()
    for item in symbols:
        norm = item.upper().strip()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        yield norm


def _resolve_primary_price(sym_data: dict) -> float | None:
    timeframes = sym_data.get("timeframes") or {}
    primary = None
    if isinstance(timeframes, dict):
        primary = timeframes.get("1h")
        if not isinstance(primary, dict):
            primary = next((block for block in timeframes.values() if isinstance(block, dict)), None)
    if not isinstance(primary, dict):
        return None
    last = primary.get("last")
    if not isinstance(last, dict):
        return None
    price = last.get("close")
    return float(price) if isinstance(price, (int, float)) else None


def generate_signals(
    symbols: Iterable[str],
    timeframes: List[str],
    bars_per_tf: int,
    data_root: Path,
) -> None:
    for symbol in _iter_symbols(symbols):
        sym_data = extract_symbol(symbol, tfs=timeframes, bars_per_tf=bars_per_tf)
        consensus = multi_tf_consensus(sym_data)
        sym_data["consensus"] = consensus
        ai_payload = ai_trade_signal(deepcopy(sym_data))
        price = _resolve_primary_price(sym_data)
        log_signal(
            symbol=symbol,
            ai_payload=ai_payload,
            consensus=consensus,
            context=deepcopy(sym_data),
            price=price,
            root=data_root,
        )
        log_entry_gap(
            symbol=symbol,
            ai_payload=ai_payload,
            context=deepcopy(sym_data),
            price=price,
            root=data_root,
        )
        print(f"[cycle] logged signal for {symbol} (price={price})")


def run_cycle(
    data_root: Path,
    horizon_minutes: int,
    calibration_path: Path,
    summary_path: Path,
    symbols: Iterable[str],
    timeframes: List[str],
    bars_per_tf: int,
) -> Tuple[str, dict]:
    generate_signals(symbols, timeframes, bars_per_tf, data_root)
    summary_text, summary_stats, _ = run_summary(
        root=data_root,
        horizon_minutes=horizon_minutes,
        return_results=True,
        calibration_path=calibration_path,
    )
    summary_path.write_text(summary_text, encoding="utf-8")
    print(f"[cycle] backtest summary written to {summary_path}")
    print(f"[cycle] calibration info written to {calibration_path}")
    return summary_text, summary_stats


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run full data collection + backtest cycle.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("data"),
        help="Data lake root directory (default: data)",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=5,
        help="Backtest evaluation horizon in minutes (default: 5)",
    )
    parser.add_argument(
        "--calibration-output",
        type=Path,
        default=Path("analytics/threshold_suggestions.json"),
        help="Path (relative to data root) to write threshold suggestions (default: analytics/threshold_suggestions.json)",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("analytics/backtest_summary.txt"),
        help="Path (relative to data root) to write backtest summary (default: analytics/backtest_summary.txt)",
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=SYMBOLS,
        help="Override symbols list (default: configured symbols in prover.py)",
    )
    parser.add_argument(
        "--timeframes",
        nargs="*",
        default=TIMEFRAMES,
        help="Override timeframes list (default: configured TIMEFRAMES)",
    )
    parser.add_argument(
        "--bars-per-tf",
        type=int,
        default=BARS_PER_TF,
        help="Number of candles to fetch per timeframe (default: prover.BARS_PER_TF)",
    )

    args = parser.parse_args(argv)
    data_root = args.root.resolve()
    paths = DataLakePaths(root=data_root).ensure_all()
    print(f"[cycle] data lake root -> {paths.root}")

    calibration_path = args.calibration_output
    if not calibration_path.is_absolute():
        calibration_path = data_root / calibration_path
    summary_path = args.summary_output
    if not summary_path.is_absolute():
        summary_path = data_root / summary_path
    calibration_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    run_cycle(
        data_root=data_root,
        horizon_minutes=args.horizon,
        calibration_path=calibration_path,
        summary_path=summary_path,
        symbols=args.symbols,
        timeframes=list(dict.fromkeys(args.timeframes)),
        bars_per_tf=args.bars_per_tf,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
