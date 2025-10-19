import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def parse_args():
    p = argparse.ArgumentParser(description="Seasonality spiral for recurring time-series")
    p.add_argument("--csv", required=True, help="Path to CSV with a date column and (optionally) a numeric value column.")
    p.add_argument("--date-col", dest="date_col", required=True, help="Name of the date column in --csv")
    p.add_argument("--value-col", dest="value_col", required=False, help="Numeric value column. If omitted, use --agg=count")
    p.add_argument("--freq", choices=["M","W","D","Q"], default="M", help="M=month, W=week, D=day, Q=quarter")
    p.add_argument("--agg", choices=["sum","mean","count"], default="sum", help="Aggregation used after resampling")
    p.add_argument("--transform", choices=["none","index100","yoy","zscore","rolling"], default="none")
    p.add_argument("--rolling-window", type=int, default=4, help="Window for --transform=rolling")
    p.add_argument("--title", default="Signal Spiral")
    p.add_argument("--out", default="out_spiral.png", help="Output image path")
    return p.parse_args()

def seasonal_periods(freq: str) -> int:
    return {"M":12, "W":52, "D":365, "Q":4}[freq]

def angle_and_labels(dates: pd.Series, freq: str):
    if freq == "M":
        k = dates.dt.month
        labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        ticks = np.arange(12) / 12 * 2*np.pi
    elif freq == "W":
        k = dates.dt.isocalendar().week.astype(int).clip(1,52)
        labels = ["W1","W13","W26","W39","W52"]
        ticks = np.array([1,13,26,39,52]) / 52 * 2*np.pi
    elif freq == "D":
        k = dates.dt.dayofyear.clip(1,365)
        labels = ["Jan","Apr","Jul","Oct"]
        ticks = np.array([1,91,182,274]) / 365 * 2*np.pi
    else:  # Q
        k = dates.dt.quarter
        labels = ["Q1","Q2","Q3","Q4"]
        ticks = np.arange(4) / 4 * 2*np.pi
    theta = (k - 1) / seasonal_periods(freq) * 2*np.pi
    return theta.to_numpy(), ticks, labels

def apply_transform(s: pd.Series, freq: str, transform: str, window: int) -> pd.Series:
    if transform == "none":
        return s
    if transform == "index100":
        base = s.iloc[0] if len(s) else 1.0
        return (s / (base if base != 0 else 1.0)) * 100.0
    if transform == "yoy":
        per = seasonal_periods(freq)
        return s.pct_change(periods=per) * 100.0
    if transform == "zscore":
        mu, sd = s.mean(), s.std(ddof=0)
        return (s - mu) / (sd if sd else 1.0)
    if transform == "rolling":
        return s.rolling(window=max(1,window), min_periods=1).mean()
    return s

def main():
    args = parse_args()

    # 1) Load CSV and normalize column names
    df = pd.read_csv(args.csv, parse_dates=[args.date_col]).rename(columns={args.date_col: "date"})
    df = df.sort_values("date")

    # 2) Decide value column / counting mode
    if args.agg == "count" and args.value_col is None:
        df["value"] = 1.0
        valcol = "value"
    else:
        if args.value_col is None:
            raise SystemExit("--value-col is required unless --agg=count")
        valcol = args.value_col
        df[valcol] = pd.to_numeric(df[valcol], errors="coerce").fillna(0.0)

    # 3) Resample to chosen frequency
    rule = {"M":"MS", "W":"W-MON", "D":"D", "Q":"QS"}[args.freq]
    resampler = df.set_index("date")[valcol].resample(rule)
    if args.agg == "sum":
        s = resampler.sum()
    elif args.agg == "mean":
        s = resampler.mean()
    else:  # count
        s = resampler.sum()

    s = s.dropna()
    s = apply_transform(s, args.freq, args.transform, args.rolling_window)

    # 4) Prepare for plotting
    out = s.reset_index().rename(columns={valcol: "value"})
    out["date"] = pd.to_datetime(out["date"])

    theta, ticks, labels = angle_and_labels(out["date"], args.freq)
    vals = out["value"].to_numpy()
    vmin, vmax = np.nanmin(vals), np.nanmax(vals)
    rng = (vmax - vmin) if (vmax - vmin) != 0 else 1.0
    r = (vals - vmin) / rng + 0.5  # keep inner radius off center

    # 5) Plot spiral
    plt.figure(figsize=(8,8))
    ax = plt.subplot(111, polar=True)
    ax.plot(theta, r)
    ax.set_title(args.title)
    ax.set_yticklabels([])
    if len(labels) <= 12:
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
    plt.tight_layout()
    plt.savefig(args.out, dpi=180)
    print(f"Saved {args.out}")

if __name__ == "__main__":
    main()
