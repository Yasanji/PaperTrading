# Sleeve A: development results

Run once on 5 October 2026, over January 2000 to December 2012, with the rules in PREREGISTRATION.md. The hold-out from January 2013 had not been run when these results were committed.

## Development test

| Period | Return a year | Volatility | Sharpe ratio | Newey-West t |
| --- | --- | --- | --- | --- |
| 2000-2012 | 3.16% | 5.4% | 0.59 | 2.22 |
| 2000-2006 | 4.51% | 5.1% | 0.88 | 2.41 |
| 2007-2012 | 1.59% | 5.7% | 0.28 | 0.73 |

The return after costs is positive with a t-statistic above 2 and positive in both halves, so the sleeve passes. The worst calendar year was 2008, at -9.7%.

## Diversification test

| | Sharpe ratio |
| --- | --- |
| Trend alone | 0.33 |
| Currency carry alone | 0.37 |
| Trend and carry at equal risk | 0.48 |

The monthly correlation between carry and trend is -0.04. The combined book has a higher Sharpe ratio than trend alone, so the sleeve passes.

| | 2005 | 2006 | 2007 | 2008 | 2009 | 2010 | 2011 | 2012 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Trend | +5.0 | +2.1 | +2.5 | +6.3 | -4.2 | +2.3 | -0.1 | -1.5 |
| Carry | +5.0 | +0.5 | +4.8 | -9.4 | +6.4 | +0.6 | +0.9 | +6.4 |

## Amendment 1

Made on 5 October 2026, after the development results and before the hold-out. The pre-registration gives the overlap for the diversification test as 2004-2012. Trend's futures data starts in January 2004, and its signal needs a year of prices and its volatility scaling six months of returns, so the overlap starts in July 2005. The rules are unchanged.

## Implementation notes

Fixed in the code before the development run: trend is rebuilt with the rules of the earlier paper (pairs/part4/trend_dev.py) on the same 15 futures; transaction costs are charged on the first day of each holding month; the interest differential for a month is the average of that month's rates.
