# Signal Spiral
Turn any recurring time-series into a seasonality spiral (month/week/day). Built for recruiting, product, and ops metrics.

## Examples this fits
- Recruiting: applications per week, interviews per month, offer acceptance rate, time-to-hire.
- Product/Growth: signups per week, DAU/WAU/MAU, retention cohorts.
- Ops/System dynamics: ticket arrivals per day, cycle time medians, backlog size.

## Data format
CSV with at least a date column and a numeric value column.

```csv
date,value
2024-01-01,123
2024-02-01,140
