# Sleeve A: hold-out results

Run once on 5 October 2026, over January 2013 to September 2026, with the rules in PREREGISTRATION.md and the development results already committed.

| Hold-out, 2013 to September 2026 | |
| --- | --- |
| Return a year | 0.19% |
| Volatility | 5.4% |
| Sharpe ratio | 0.03 |
| Newey-West t | 0.12 |

| 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -1.5 | +0.9 | -3.9 | +4.1 | -0.3 | -2.0 | +4.7 | -8.1 | +4.8 | -0.2 | -0.9 | -2.6 | -1.4 | +8.9 |

The return after costs is positive, so the sleeve passes the hold-out rule in PREREGISTRATION.md and stays in the book.

## Note on the hold-out rule

The pass is fragile. The Sharpe ratio of 0.03 is indistinguishable from zero, and the period's return is positive only because of 2026 so far. The rule, a positive return after costs, set too low a bar for a 14-year hold-out. It is not changed after the result. Later pre-registrations set a stronger hold-out rule, and the sleeve's share of the book's risk, set in the portfolio pre-registration before the book goes live, will take this result into account.

## Implementation notes

Fixed in the code before the hold-out run: sterling's three-month rate after February 2026 is the Bank of England's SONIA rate averaged by month, as in PREREGISTRATION.md; where a country's latest monthly rate was not yet published (Japan and Australia for September 2026), the previous month's rate is carried forward for one month.
