import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (ensures 3D proj is registered)
from mpl_toolkits.mplot3d.art3d import Line3DCollection

def parse_args():
    p = argparse.ArgumentParser(description="3D climate-style spiral (helix) for monthly time series")
    p.add_argument("--csv", required=True, help="CSV with a date column and numeric value column")
    p.add_argument("--date-col", dest="date_col", required=True, help="Date column name")
    p.add_argument("--value-col", dest="value_col", required=True, help="Numeric value column name")
    p.add_argument("--agg", choices=["sum","mean","last"], default="mean", help="Aggregation after monthly resample")
    p.add_argument("--title", default="3D Signal Spiral")
    p.add_argument("--out", default="out_spiral3d.png", help="Output image path")
    p.add_argument("--r-min", type=float, default=0.6, help="Inner radius (keeps line off the center)")
    p.add_argument("--r-max", type=float, default=1.0, help="Outer radius (scale to this)")
    p.add_argument("--z-year-scale", type=float, default=1.0, help="Z spacing per year (1.0 ≈ one unit per year)")
    return p.parse_args()

def monthly_series(df, date_col, value_col, agg):
    rule = "MS"  # month start
    s = df.set_index(date_col)[value_col]
    if agg == "sum":
        s = s.resample(rule).sum()
    elif agg == "mean":
        s = s.resample(rule).mean()
    else:
        s = s.resample(rule).last()
    s = s.dropna()
    return s.reset_index().rename(columns={value_col: "value", date_col: "date"})

def to_helix_coords(dates, values, rmin=0.6, rmax=1.0, z_year_scale=1.0):
    # angle = month (1..12) mapped to 0..2π
    months = dates.dt.month.values
    theta = (months - 1) / 12.0 * 2.0 * np.pi
    # z = fractional year (year + month/12) scaled
    years = dates.dt.year.values + (months - 1) / 12.0
    z = (years - years.min()) * z_year_scale
    # radius = normalized value mapped into [rmin, rmax]
    v = values.astype(float)
    vmin, vmax = np.nanmin(v), np.nanmax(v)
    span = (vmax - vmin) if (vmax - vmin) != 0 else 1.0
    r = rmin + (v - vmin) / span * (rmax - rmin)
    # to Cartesian
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y, z, v

def line3d_with_colormap(ax, x, y, z):
    # Build line segments between consecutive points
    pts = np.vstack([x, y, z]).T
    segs = np.concatenate([pts[:-1, None, :], pts[1:, None, :]], axis=1)
    # Color by time (z) like NASA climate spiral
    norm = Normalize(vmin=np.nanmin(z), vmax=np.nanmax(z))
    lc = Line3DCollection(segs, cmap=cm.plasma, norm=norm, linewidth=2.0)
    mids = (z[:-1] + z[1:]) / 2.0
    lc.set_array(mids)
    ax.add_collection(lc)
    # Autoscale axes to data
    ax.set_xlim(np.nanmin(x), np.nanmax(x))
    ax.set_ylim(np.nanmin(y), np.nanmax(y))
    ax.set_zlim(np.nanmin(z), np.nanmax(z))
    return lc

def main():
    args = parse_args()
    df = pd.read_csv(args.csv, parse_dates=[args.date_col])
    df = df[[args.date_col, args.value_col]].dropna().sort_values(args.date_col)
    m = monthly_series(df, args.date_col, args.value_col, args.agg)

    x, y, z, v = to_helix_coords(m["date"], m["value"],
                                 rmin=args.r_min, rmax=args.r_max,
                                 z_year_scale=args.z_year_scale)

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    line3d_with_colormap(ax, x, y, z)

    # Aesthetics similar to NASA style
    ax.set_title(args.title)
    ax.set_xticks([]); ax.set_yticks([])       # hide XY ticks
    ax.set_zlabel("Time →")                    # Z is time progression
    ax.grid(False)
    # Faint reference ring at median radius on z=0
    ang = np.linspace(0, 2*np.pi, 200)
    r0 = (args.r_min + args.r_max) / 2.0
    ax.plot(r0*np.cos(ang), r0*np.sin(ang), np.full_like(ang, z.min()), alpha=0.1, lw=1)

    plt.tight_layout()
    plt.savefig(args.out, dpi=180)
    print(f"Saved {args.out}")

if __name__ == "__main__":
    main()
