# Book: Amendment 1

Dated 8 October 2026, after day 1 of the dry run and before any order is sent to the paper account. The signals, costs and pass marks are unchanged.

## 1. Pod 1 sizing

At the incubation scale of 0.25, Pod 1's rates and equity index legs round to zero contracts, so only the currency legs trade. While the book trades the paper account (DUT139070), Pod 1 runs at full risk: `config.SCALE[1] = 1.0`. This tests every leg at the size the pod was designed for. Before any live order, the scale goes back to the pre-registered incubation level unless a further amendment says otherwise. Results from the paper period are reported at full risk and are not rescaled.

## 2. Price data

The live IB account has no futures market data subscriptions, and IB will not activate them until the account is funded. Until then, prices for targets, sizing and reconciliation marks come from Yahoo Finance (`futures_ib.py --yahoo-only`, `execute.py NO_IB_DATA = True`). IB is used only to send orders and report fills and positions. Fill prices from IB are the record of execution; Yahoo prices are the record of signals. Differences between the two are logged by reconciliation. When IB data is active, this section lapses and the change is recorded in the events table.
