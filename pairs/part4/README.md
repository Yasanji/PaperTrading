# Part 4: What survives honest testing

This folder holds the code for Part 4 of the series and for the working paper *What Survives Honest Testing? A Pre-Registered Test of Eleven Trading Signals*, in which eleven signals in European equities and global futures were each tested under rules fixed before they were run, first on a development decade (2013 to 2022), on unseen crisis years (2008 to 2012) for those that qualified, and once on a hold-out period (2023 to 2026). The rules and results are listed in `PREREGISTRATION.md`.

## Run order

The scripts are research code, written to run from one working directory with a `msb/` subfolder, and each reads the files written by earlier steps and saves its results as pickles in `msb/`.

1. **Data.** `get_long.py` (STOXX 600 prices from 2009), `get_ext.py` (equities and the 15 futures from 2004), `get_rates.py` (Treasury and OECD rates), and `map_isin.py`, which matches the FCA and AMF short-position files to the universe. The two short-position files are downloaded by hand from the FCA and AMF websites into `shorts/`. The futures positioning data comes from `../part5/tsmom_data.py`.
2. **Signal tests on 2013 to 2022.** `mom_test.py`, `rev_test.py`, `si_test.py`, `pairs_dev.py` (with `model_600_long.py`), `lowvol_test.py`, `indmom_test.py`, `trend_dev.py`, `carry_test.py`, `value_eq.py`, `value_fut.py` and `volmanaged.py`.
3. **Crisis years, 2008 to 2012.** `pre_trend.py`, `pre_lowvol.py` and `pre_mom.py`.
4. **Hold-out, 2023 to 2026.** `holdout.py`, run once.
5. **Checks and statistics.** `trend_etf.py` reruns trend on exchange-traded funds tracking the same markets; `sensitivity/` holds the cost, delay and borrow variants; `paper_stats.py` produces the deflated Sharpe ratios, bootstrap intervals, power table, Newey-West checks, the Reality Check and SPA tests, the factor alphas and the stress tables; `paper_figs.py` draws the paper's figures.

## Data and its limits

Prices come from Yahoo Finance, using today's index constituents, so survivorship bias is present and grows further back in time. The continuous futures series are not adjusted for contract rolls; the exchange-traded fund check indicates that this understated trend's results. The ICE BofA high-yield spread needed for credit carry is available free only from October 2023, so that part of the carry test could not be run.
