# Pod 3: Amendment 1

Dated 8 October 2026, before any prediction for the November 2026 review is committed. It changes how MSCI Europe predictions are made. The trade, sizing, costs and pass marks are unchanged.

## 1. Why

The pre-registration cites the August 2023 MSCI methodology, with buffers of two-thirds and 1.5 times the cut-off, or one-half and 1.8 times at a light rebalancing. The current methodology is the August 2026 version. Under it every review in February, May, August and November is a full review, and the one-half and 1.8 buffers apply only if MSCI declares a light rebalancing under market stress.

## 2. Rules applied

From the MSCI GIMI Methodology, August 2026:

1. The Global Minimum Size Reference for developed-market Standard indexes was USD 16.28 billion on 20 July 2026. Its range is 0.5 to 1.15 times the reference. For each review the reference is scaled by the change in the MSCI World index (iShares URTH) since 20 July, and the scaling is recorded with the prediction.
2. Each market's cut-off is the full market value of the company ranked at that market's current number of Standard index companies, among Standard and Small Cap constituents, kept within the range in rule 1.
3. A current constituent is predicted for deletion when its full market value is below 1.05 times two-thirds of its market's cut-off, and placed on a watch list between 1.05 and 1.20 times.
4. A Small Cap constituent is predicted for addition when its full market value is at least 0.97 times 1.5 times the cut-off and its free float value is at least half the cut-off, and placed on a watch list between 0.85 and 0.97 times.
5. Prices are the average over the last 10 business days of the month before the review, up to the commitment date.

The factors 1.05 and 0.97 in rules 3 and 4 were chosen after seeing how the method ranked the actual changes at the May and August 2026 reviews (section 3). They are fixed from this date.

## 3. Check on past reviews

Membership before each review was rebuilt from current fund holdings and MSCI's published change lists, and prices were taken from each review's price window.

| Review | Predicted deletions | Right | Actual deletions | Predicted additions | Right | Actual additions |
| --- | --- | --- | --- | --- | --- | --- |
| May 2026 | 8 | 7 | 9 | 3 | 1 | 3 |
| August 2026 | 1 | 1 | 10 | 1 | 1 | 1 |

In August three more actual deletions were on the watch list. Five of August's ten deletions were corporate events or names the data does not cover (for example Sunbelt Rentals, which moved its listing to the US). This check is in-sample, since it was used to set the factors.

## 4. Limits

Not modelled: liquidity, foreign room, MSCI's adjustment of the number of companies to its 85% coverage target, corporate events and IPOs outside the Small Cap index. Market values are from Yahoo Finance and free float values from the Xtrackers MSCI Europe and MSCI Europe Small Cap fund weights.

## 5. Timetable for November 2026

MSCI announces on 11 November 2026, effective after the close on 30 November. The final prediction is run after the close on 30 October and committed before the open on 2 November, 20 trading days before the effective date. The earlier lists in `pods/pod3_msci/data/` are preliminary.
