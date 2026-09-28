# Live pairs runner

A rules-based paper runner for the SAF and SIE pair. It reuses the existing
modules in this folder: `ibkr.py` (Client Portal Web API client), `statarb.py`
(the point-in-time engine), and `data.py` (history parsing). It adds three
files:

- `live_config.py` — account, the two contract ids, strategy parameters, risk
  caps, and the two safety flags.
- `find_conids.py` — prints contract-id candidates so you can fill the config.
- `live_pairs.py` — one pass: pull history, compute the signal, size the legs,
  run the pre-trade checks, reconcile against the account, place or log orders.

## Safety

`paper_only` refuses to run if the account id does not start with DU.
`dry_run` logs the orders it would place and places nothing. Both start on.

## Steps

1. Create a paper account in the Client Portal and note its id, which starts
   with DU.

2. Check Java is present, and install it if not:

       java -version
       brew install openjdk   # only if the check fails

3. Download and start the Client Portal gateway:

       curl -fL https://download2.interactivebrokers.com/portal/clientportal.gw.zip -o gw.zip
       unzip gw.zip -d clientportal.gw
       cd clientportal.gw && bin/run.sh root/conf.yaml

4. Open https://localhost:5000, accept the certificate warning, and log in with
   your paper username and password. You should see "Client login succeeds".

5. Install the dependency:

       pip install requests

6. Find the contract ids, then set them in `live_config.py`:

       python find_conids.py

   Pick the rows for the EUR listings of Safran and Siemens, and copy their
   conids into `conid_y` and `conid_x`. Set `account` to your DU id.

7. Dry run and read the log:

       python live_pairs.py
       cat live_pairs.log

   It prints the z-score, the hedge ratio, the target, and the orders it would
   place.

8. When the dry run looks right over several sessions, set `dry_run = False` in
   `live_config.py` to let it place paper orders. Keep `paper_only = True`.

## Running daily

`live_pairs.py` runs one pass. To trade the daily signal, call it once a day
after both markets close, with cron or a small scheduler. It stores the position
in `live_state.json`, so the state carries across runs.

## Notes

The gateway serves history for instruments your account has data permissions
for. If `find_conids.py` returns nothing or history comes back empty for a
European name, the paper account is likely missing the market-data permission
for that exchange; add it in the Client Portal or use a name you do have data
for while testing.

The engine recomputes an OLS hedge ratio each day. A sanity bound on that ratio,
periodic re-checking of the cointegration test, and volatility-based sizing are
the natural next additions, and they line up with the later parts of the series.
