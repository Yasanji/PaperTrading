# Pre-registration log

Each test below was written down and dated in the project's working notes before it was run, and its rules were not changed afterwards. This file was committed after the tests, so the dates rest on those notes and not on the commit history. Tests added from here on will be committed before they are run, so that the commit time records when each was fixed.

| # | Test | Fixed | Period | Pass mark | Result |
|---|---|---|---|---|---|
| 1 | Industry-neutral momentum | 1 Oct 2026 | 2013-2022 | Positive, t > 2, positive in both halves | Failed (Sharpe 0.30); kept as a weak signal |
| 2 | Short-term reversal | 1 Oct 2026 | 2013-2022 | As above | Failed; negative in 2018-2022, so excluded |
| 3 | Disclosed short interest | 1 Oct 2026 | 2013-2022 | As above | Failed; excluded |
| 4 | Pairs signal | 1 Oct 2026 | 2013-2022 | As above | Failed (Sharpe 0.02); excluded |
| 5 | Low volatility | 1 Oct 2026 | 2013-2022 | As above | Passed (Sharpe 0.72, t 2.3) |
| 6 | Industry momentum | 1 Oct 2026 | 2013-2022 | As above | Failed; excluded |
| 7 | Futures trend | 1 Oct 2026 | 2013-2022 | As above | Passed (Sharpe 0.80, t 2.5) |
| 8 | Carry (currencies, bonds, credit) | 1 Oct 2026 | 2013-2022 | As above | Currencies and bonds negative in 2018-2022; credit untestable; excluded |
| 9 | Value proxy, equities | 1 Oct 2026 | 2015-2022 | As above | Failed; excluded |
| 10 | Value proxy, futures | 1 Oct 2026 | 2013-2022 | As above | Failed; excluded |
| 11 | Volatility-managed equity index | 1 Oct 2026 | 2013-2022 and 2008-2012 | Positive alpha, t > 2, positive in both halves and in 2008-2012 | Failed |
| Check | Crisis-years check | 1 Oct 2026 | 2008-2012 | A signal losing money is removed | Trend kept; low volatility and momentum removed |
| Final | Hold-out | 2 Oct 2026 | 2023-2026 | Positive return after costs | Passed (trend, Sharpe 0.77) |

The combination rule, also fixed on 1 October 2026 before any combined result existed, admitted a signal to the combined book if it was positive after costs in both halves of the development decade.
