import argparse, pandas as pd, numpy as np, matplotlib.pyplot as plt

def parse_args():
    p = argparse.ArgumentParser(description="Seasonality spiral for recurring time-series")
    p.add_argument("--csv", required=True)
    p.add_argument("--date-col", required=True)
    p.add_argument("--value-col", required=False, help="Numeric value column. If omitted and --agg=count, rows are counted.")
    p.add_argument("--freq", choices=["M","W","D","Q"], default="M", help="M=month, W=week, D=day, Q=quarter")
    p.add_argument("--agg", choices=["sum","mean","count"], default="sum")
    p.add_argument("--transform", choices=["none","index100","yoy","zscore","rolling"], default="none")
    p.add_argument("--rolling-window", type=int, default=4, help="Used when --transform=rolling")
    p.add_argument("--title", default="Signal Spiral")
    p.add_argument("--out", default="out_spiral.png")
    return p.parse_args()

def seasonal_periods(freq):
    return {"M":12, "W":52, "D":365, "Q":4}[freq]

def angle_and_labels(df, freq):
    if freq == "M":
        k = df["date"].dt.month
        labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        ticks = np.arange(12) / 12 * 2*np.pi
    elif freq == "W":
        k = df["date"].dt.isocalendar().week.astype(int).clip(1,52)
        labels = ["W1","W13","W26","W39","W52"]
        ticks = np.array([1,13,26,39,52]) / 52 * 2*np.pi
    elif freq == "D":
        k = df["date"].dt.dayofyear.clip(1,365)
        labels = ["Jan","Apr","Jul","Oct"]
        ticks = np.array([1,91,182,274]) / 365 * 2*np.pi
    else:  # Q
        k = df["date"].dt.quarter
        labels = ["Q1","Q2","Q3","Q4"]
        ticks = np.arange(4) / 4 * 2*np.pi
    theta = (k - 1) / seasonal_periods(freq) * 2*np.pi
    return theta, ticks, labels

def apply_transform(s, freq, transform, window):
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
    df = pd.read_csv(args.csv, parse_dates=[args.date-col]).rename(columns={args.date-col:"date"})
    df = df.sort_values("date")

    # aggregate if needed
    if args.agg == "count":
        df["value"] = 1.0
        valcol = "value"
    else:
        valcol = args.value_col
        if valcol is None:
            raise SystemExit("--value-col is required unless --agg=count")

    # resample to desired freq
    rule = {"M":"MS", "W":"W-MON", "D":"D", "Q":"QS"}[args.freq]
    g = df.set_index("date")[valcol].resample(rule)

    if args.agg == "sum":
        s = g.sum()
    elif args.agg == "mean":
        s = g.mean()
    else:  # count
        s = g.sum()

    s = s.dropna()
    s = apply_transform(s, args.freq, args.transform, args.rolling_window)

    out = s.reset_index().rename(columns={0:"value"})
    out["date"] = pd.to_datetime(out["date"])
    theta, ticks, labels = angle_and_labels(out, args.freq)

    vals = out[valcol if valcol in out.columns else "value"].values if valcol in out.columns else out["value"].values
    vmin, vmax = np.nanmin(vals), np.nanmax(vals)
    rng = (vmax - vmin) if (vmax - vmin) != 0 else 1.0
    r = (vals - vmin)/rng + 0.5

    import matplotlib.pyplot as plt
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
