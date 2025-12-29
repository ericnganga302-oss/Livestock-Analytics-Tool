"""
metrics.py
Pure functions for livestock metrics used by app.py and unit tests.
"""
from datetime import datetime
from math import inf
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd


def safe_div(a: float, b: float) -> Optional[float]:
    try:
        return a / b
    except Exception:
        return None


def compute_metrics(initial_wt: float,
                    current_wt: float,
                    days: int,
                    feed_used: float,
                    price_per_kg: float,
                    feed_cost: float) -> dict:
    """
    Compute key KPIs from summary inputs.
    """
    weight_gain = current_wt - initial_wt
    adg = safe_div(weight_gain, days) if days and days > 0 else None
    fcr = safe_div(feed_used, weight_gain) if weight_gain and weight_gain > 0 else None
    revenue_now = current_wt * price_per_kg
    costs = feed_used * feed_cost
    profit_now = revenue_now - costs
    cost_per_kg_gain = safe_div(costs, weight_gain) if weight_gain and weight_gain > 0 else None

    return {
        "weight_gain": weight_gain,
        "adg": adg,
        "fcr": fcr,
        "revenue_now": revenue_now,
        "costs": costs,
        "profit_now": profit_now,
        "cost_per_kg_gain": cost_per_kg_gain,
    }


def estimate_days_to_target(current_wt: float, target_wt: float, adg: Optional[float]) -> float:
    """
    Returns estimated days to reach target weight.
    Returns 0 if already at/above target.
    Returns inf if adg is None or <= 0.
    """
    if target_wt <= current_wt:
        return 0.0
    if adg is None or adg <= 0:
        return inf
    remaining = target_wt - current_wt
    return remaining / adg


def parse_date_column(series: pd.Series) -> pd.Series:
    """
    Parse date-like series into datetime64[ns]; if values look like integers (days),
    they are returned as-is (numeric).
    """
    # Try parse to datetime; if fails, leave numeric
    try:
        s = pd.to_datetime(series)
        return s
    except Exception:
        # maybe it's already numeric days
        return series


def compute_adg_from_timeseries(dates: List, weights: List[float]) -> Tuple[Optional[float], pd.DataFrame]:
    """
    Compute ADG (kg/day) using linear regression (least squares slope) on the provided
    time series of dates and weights.

    Inputs:
    - dates: list of date-like items (datetime/date strings) or numeric days
    - weights: list of weights (floats)

    Returns:
    - adg (slope in kg/day) or None if insufficient data
    - dataframe with columns ['day', 'weight'] where day is numeric days since first point
    """
    if len(weights) < 2:
        return None, pd.DataFrame({"day": [], "weight": []})

    df = pd.DataFrame({"date": dates, "weight": weights})
    # Try to parse dates; if parsing works, compute day offsets
    try:
        df["date_parsed"] = pd.to_datetime(df["date"])
        df = df.sort_values("date_parsed")
        df["day"] = (df["date_parsed"] - df["date_parsed"].iloc[0]).dt.total_seconds() / (24 * 3600)
    except Exception:
        # treat date column as numeric days
        df = df.sort_values("date")
        df["day"] = pd.to_numeric(df["date"]) - float(pd.to_numeric(df["date"]).iloc[0])

    # ensure numeric
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df = df.dropna(subset=["weight", "day"])
    if len(df) < 2:
        return None, pd.DataFrame({"day": [], "weight": []})

    x = df["day"].to_numpy()
    y = df["weight"].to_numpy()

    # Fit linear model y = m*x + c; slope m is ADG (kg/day)
    m, c = np.polyfit(x, y, 1)
    adg = float(m)
    return adg, df[["day", "weight"]].reset_index(drop=True)
