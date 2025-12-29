import math
from metrics import compute_metrics, estimate_days_to_target, compute_adg_from_timeseries

def test_compute_metrics_basic():
    m = compute_metrics(initial_wt=100, current_wt=150, days=50, feed_used=200, price_per_kg=200, feed_cost=40)
    assert m["weight_gain"] == 50
    assert round(m["adg"], 6) == 1.0
    assert round(m["fcr"], 6) == 4.0
    assert m["revenue_now"] == 150 * 200
    assert m["costs"] == 200 * 40

def test_estimate_days_to_target():
    days = estimate_days_to_target(current_wt=200, target_wt=300, adg=0.5)
    assert days == 200.0

    # already at/above target
    assert estimate_days_to_target(300, 300, 1.0) == 0.0

    # no adg
    assert estimate_days_to_target(200, 300, None) == math.inf

def test_compute_adg_from_timeseries_numeric_days():
    days = [0, 10, 20]
    weights = [100, 110, 120]
    adg, df = compute_adg_from_timeseries(days, weights)
    assert round(adg, 6) == 1.0
    assert len(df) == 3

def test_compute_adg_from_timeseries_dates():
    dates = ["2025-01-01", "2025-01-11", "2025-01-21"]
    weights = [100, 110, 120]
    adg, df = compute_adg_from_timeseries(dates, weights)
    assert round(adg, 6) == 1.0
    assert len(df) == 3
