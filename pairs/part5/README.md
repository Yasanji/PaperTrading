# Part 5: Flows and positioning

This folder covers speculators' positioning in futures, taken from the CFTC Commitments of Traders reports, and why it matters to use that data only from the date it was published. The work was first numbered Part 4 and was renumbered when the series changed.

## Scripts

- `get_cot.py` downloads the Commitments of Traders history.
- `pit_demo.py` builds speculators' net positioning for six futures markets and downloads prices.
- `pit_bt.py` trades the same weekly signal from three dates: Tuesday (the date each report describes, which uses information not yet published), the Friday close after publication, and the following Monday close.
- `pit_chart.py` draws that comparison.
- `pit_contra.py` runs the pre-registered contrarian test, fading speculators on 2010 to 2018.
- `tsmom_data.py` and `tsmom_crowd.py` run the pre-registered test of whether crowded positioning hurts 12-month trend following across 15 markets.

## Results

Dating trades to Tuesday flattered the result by about 1% a year over 2019 to 2026, in the expected direction, although the difference is not statistically significant (a Newey-West t of 0.7 on the weekly differences). The contrarian test, fixed on 29 September 2026, failed on 2010 to 2018 at -0.9% a year (t of -0.6), having looked promising only on the period that suggested it. The crowding test, fixed on 1 October 2026, found that crowded trend positions earned 2.6% a year less than uncrowded ones (t of -1.6), negative in both halves, which falls short of the pass mark of t below -2.

Yahoo continuous futures are not adjusted for contract rolls, which adds noise, most of all in energy markets.
