"""
CSV import module for loading stock symbols and data.

Provides functionality to:
  - Load stock symbols from a CSV file
  - Import stock data with custom fields
  - Validate and parse CSV inputs
"""
from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def import_symbols_from_csv(csv_path: str) -> list[str]:
    """
    Load stock symbols from a CSV file.

    The CSV file should have a 'symbol' column (case-insensitive).
    Other columns are ignored.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of stock symbols (uppercase)

    Raises:
        FileNotFoundError: If the CSV file does not exist
        ValueError: If the CSV has no 'symbol' column
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    symbols = []
    try:
        df = pd.read_csv(csv_path)

        # Find 'symbol' column (case-insensitive)
        symbol_col = None
        for col in df.columns:
            if col.lower() == "symbol":
                symbol_col = col
                break

        if symbol_col is None:
            raise ValueError(
                f"CSV file must contain a 'symbol' column. Found columns: {list(df.columns)}"
            )

        # Extract and validate symbols
        for idx, row in df.iterrows():
            sym = str(row[symbol_col]).strip().upper()
            if sym and sym not in symbols:  # Avoid duplicates
                symbols.append(sym)
            elif not sym:
                logger.warning(f"Row {idx + 2}: Empty symbol value, skipping")

        logger.info(f"Imported {len(symbols)} symbols from {csv_path}")
        return symbols

    except pd.errors.EmptyDataError:
        logger.error(f"CSV file is empty: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise


def import_stock_data_from_csv(csv_path: str) -> list[dict[str, Any]]:
    """
    Load stock data from a CSV file.

    Expects columns: symbol, name, price, change, change_pct, volume, date (optional)
    Other columns are preserved as-is.

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of dictionaries with stock data

    Raises:
        FileNotFoundError: If the CSV file does not exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    required_columns = {"symbol", "name", "price"}
    stocks = []

    try:
        df = pd.read_csv(csv_path)

        # Normalize column names (case-insensitive check)
        csv_cols_lower = {col.lower(): col for col in df.columns}
        missing = required_columns - set(csv_cols_lower.keys())

        if missing:
            raise ValueError(
                f"CSV is missing required columns: {missing}. "
                f"Found columns: {list(df.columns)}"
            )

        # Process each row
        for idx, row in df.iterrows():
            try:
                stock_dict = {}

                # Map columns (case-insensitive)
                for col in df.columns:
                    col_lower = col.lower()
                    value = row[col]

                    # Skip NaN values
                    if pd.isna(value):
                        stock_dict[col_lower] = None
                        continue

                    # Type conversion for numeric columns
                    if col_lower in ("price", "change", "change_pct", "volume", "avg_volume"):
                        try:
                            stock_dict[col_lower] = float(value) if col_lower != "volume" else int(value)
                        except (ValueError, TypeError):
                            logger.warning(
                                f"Row {idx + 2}, column '{col}': Could not convert '{value}' to numeric, using None"
                            )
                            stock_dict[col_lower] = None
                    else:
                        # Keep as string for symbol, name, date, etc.
                        stock_dict[col_lower] = str(value).strip() if value else None

                # Ensure symbol is uppercase
                if "symbol" in stock_dict and stock_dict["symbol"]:
                    stock_dict["symbol"] = stock_dict["symbol"].upper()

                # Add required fields with defaults if missing
                if "insider_net" not in stock_dict:
                    stock_dict["insider_net"] = None
                if "insider_sentiment" not in stock_dict:
                    stock_dict["insider_sentiment"] = "N/A"
                if "stage_classification" not in stock_dict:
                    stock_dict["stage_classification"] = "N/A"
                if "action_signal" not in stock_dict:
                    stock_dict["action_signal"] = "HOLD"
                if "position" not in stock_dict:
                    stock_dict["position"] = "HOLD"
                if "signal_type" not in stock_dict:
                    stock_dict["signal_type"] = "neutral"
                if "signals" not in stock_dict:
                    stock_dict["signals"] = []

                stocks.append(stock_dict)

            except Exception as e:
                logger.error(f"Error processing row {idx + 2}: {e}")
                continue

        logger.info(f"Imported {len(stocks)} stock records from {csv_path}")
        return stocks

    except pd.errors.EmptyDataError:
        logger.error(f"CSV file is empty: {csv_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise


def export_symbols_to_csv(symbols: list[str], csv_path: str) -> None:
    """
    Export stock symbols to a CSV file.

    Args:
        symbols: List of stock symbols
        csv_path: Path where the CSV file will be written
    """
    try:
        os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
        df = pd.DataFrame({"symbol": symbols})
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {len(symbols)} symbols to {csv_path}")
    except Exception as e:
        logger.error(f"Error exporting symbols to CSV: {e}")
        raise


def export_stocks_to_csv(stocks: list[dict[str, Any]], csv_path: str) -> None:
    """
    Export stock data to a CSV file.

    Args:
        stocks: List of stock dictionaries
        csv_path: Path where the CSV file will be written
    """
    try:
        os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
        df = pd.DataFrame(stocks)
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported {len(stocks)} stock records to {csv_path}")
    except Exception as e:
        logger.error(f"Error exporting stocks to CSV: {e}")
        raise
