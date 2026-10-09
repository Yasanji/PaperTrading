# Book: Amendment 1

Dated 8 October 2026, after day 1 of the dry run and before any order is sent to the paper account. The signals, costs and pass marks are unchanged.

## 1. Pod 1 sizing

At the incubation scale of 0.25, Pod 1's rates and equity index legs round to zero contracts, so only the currency legs trade. While the book trades the paper account (DUT139070), Pod 1 runs at full risk: `config.SCALE[1] = 1.0`. This tests every leg at the size the pod was designed for. Before any live order, the scale goes back to the pre-registered incubation level unless a further amendment says otherwise. Results from the paper period are reported at full risk and are not rescaled.

## 2. Price data

The live IB account has no futures market data subscriptions, and IB will not activate them until the account is funded. Until then, prices for targets, sizing and reconciliation marks come from Yahoo Finance (`futures_ib.py --yahoo-only`, `execute.py NO_IB_DATA = True`). IB is used only to send orders and report fills and positions. Fill prices from IB are the record of execution; Yahoo prices are the record of signals. Differences between the two are logged by reconciliation. When IB data is active, this section lapses and the change is recorded in the events table.

## 3. Orders over 10% of NAV

At full risk, single futures orders can exceed 10% of NAV in face value (US Treasury futures and the Canadian dollar on 8 October 2026), although their risk is far smaller. Such an order is no longer stopped outright. It is flagged in the orders file, the batch is held, and it is sent only if the batch is approved with a written reason (`approve.py ... --reason`). An order over 10% of NAV that was not flagged in the approved, checksummed orders file still trips the kill switch.

## 4. Contract check at the 60/20/20 split

Re-run on 9 October 2026 with IB Gateway (contract_check_2026-10-09.csv), after Sleeve C took 20% of Pod 1's risk. Trend trades 12 of 15 markets at 99% of its target risk (PASS); Nasdaq-100, 30-year Treasuries and gold stay out. The New Zealand dollar falls to 0.44 of a contract and is left out of currency carry under amendment 10.4. Carry still ranks all seven currencies, and a position that would fall to the New Zealand dollar is not taken, so the carry sleeve can hold five positions instead of six.
