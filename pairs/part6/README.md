# Part 6: Option payoffs (working)

`fly.py` runs the pre-registered weekly short iron butterfly on gold (GLD), priced from the Cboe gold volatility index, with a first stage that checks the pricing method against the Cboe S&P 500 Iron Butterfly Index (BFLY).

Result (fixed 1 October 2026): the pricing method tracked BFLY in timing (monthly correlation 0.90) but overstated its return by about five points a year, and the gold butterfly failed its pass mark (+1.1% a year, t of 1.3) with a worst drawdown of -13%, more than three times the 4% cap. A test priced from traded option quotes is drafted in the working notes.
