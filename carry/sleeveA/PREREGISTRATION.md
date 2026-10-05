# Sleeve A: G10 currency carry

Pre-registration, drafted 5 October 2026, before any returns are computed. Yasanji Ratnaike.

## The question

Does a carry strategy across G10 currencies earn a positive return after costs, and does it diversify the trend sleeve of the paper book? Carry, buying high-interest-rate currencies against low-interest-rate ones, is among the best documented premia across asset classes (Koijen, Moskowitz, Pedersen and Vrugt, 2018), and it tends to earn in calm markets and lose in sell-offs, when trend tends to gain.

**Disclosure.** An earlier carry test (Ratnaike, 2026) used five of these currencies (the euro, yen, sterling, Australian dollar and Canadian dollar) together with Treasury futures over 2013–2022, and lost money over 2018–2022. This test is designed around that: development uses 1999–2012, which the earlier test did not use, and four currencies (the Swiss franc, New Zealand dollar, Swedish krona and Norwegian krone) are new. The hold-out from 2013 is therefore only partly unseen for the five earlier currencies, and the trial is counted as a further strategy tried.

## Universe and data

- **Currencies:** the euro (the Deutschmark before 1999), yen, sterling, Swiss franc, Canadian dollar, Australian dollar, New Zealand dollar, Swedish krona and Norwegian krone, each against the US dollar.
- **Exchange rates:** Bank of England daily spot rates against sterling, converted to rates against the dollar, available from 1990 for all nine.
- **Interest rates:** OECD three-month interbank rates (series IR3TIB), monthly averages. The Swiss franc enters in July 1999 and the yen in April 2002, when their series begin. For sterling after the last OECD observation (February 2026), the Bank of England's SONIA rate, averaged by month, is used.
- **Coverage confirmed on 5 October 2026, before any returns were computed.**

## The strategy

1. **Signal.** At each month-end, each currency's carry is its three-month rate minus the US three-month rate, using the previous month's average rates, which are known by then.
2. **Positions.** Long the three currencies with the highest carry and short the three with the lowest, each sized inversely to its realised volatility over the previous three months, so that each position carries equal risk. The book is neutral in dollars.
3. **Returns.** The monthly return of a long position is the change in the exchange rate against the dollar plus the interest-rate differential for the month, which is the return on a currency forward under covered interest parity.
4. **Costs.** 2 basis points of each traded amount, for each leg, which reflects the spread on G10 spot and forward trades.
5. **Scaling.** The sleeve is scaled to 5% annual volatility using its realised volatility over the previous six months, as for every signal in the earlier paper.

## Periods and tests

- **Development:** January 2000 to December 2012.
- **Hold-out:** January 2013 to September 2026, run once after the development result is recorded.
- **Forward test:** live in the paper account from its start date, reported in full.

**Pass mark for development.** The sleeve passes if its return after costs is positive with a Newey–West t-statistic above 2, and positive in both halves (2000–2006 and 2007–2012). As in the earlier paper, a sleeve that is positive in both halves without reaching t = 2 qualifies for the book as a weak signal.

**Diversification test.** Over 2004–2012, when trend's data overlaps, the monthly correlation between carry and trend is reported, and the sleeve enters the book only if a book holding trend and carry at equal risk has a higher Sharpe ratio than trend alone.

**Hold-out.** The sleeve stays in the book if its hold-out return after costs is positive.

## What would count as failure

- A negative return after costs over development, or a loss in either half.
- No improvement in the combined book's Sharpe ratio over trend alone.
- A negative return after costs over the hold-out.

Each result is reported whatever it shows.

## Choices fixed here

The three-and-three long–short structure, monthly rebalancing, the three-month rates, the 2 basis point cost, the 5% volatility target and both pass marks are fixed now and will not be changed after any result is seen. Any correction to the code that makes it match these rules will be recorded as a dated amendment.
