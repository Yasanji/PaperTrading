# Part 2: does a Kalman filter help?

This folder tests the frozen Part 2 design with its 90-day rolling anchor and quarterly hedge ratio replaced by a Kalman filter on log prices, in which the hedge ratio and the level both drift a little each day, estimated only from data up to that day.

- `kalman_patch.py` holds the filter. `MEMORY = 90` sets the drift so that the anchor adapts over about 90 days, matching the rolling anchor.
- `model_v5_kalman.py` (EURO STOXX 50) and `model_600_kalman.py` (STOXX 600, ten pairs) are the Part 2 models with the filter swapped in.
- `run_kalman.py` runs both and compares them with the published results.

The first run used the textbook drift setting (Chan, 2013), which adapted so quickly that the book barely traded. The second, with the speed matched to 90 days, earned 0.2% a year from the pairs on the EURO STOXX 50 against 2.2% with the rolling anchor, and nothing on the STOXX 600 against 1.9%, so the rolling anchor was kept.
