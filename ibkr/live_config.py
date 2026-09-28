"""Settings for the live paper pairs runner.

Fill in account and the two contract ids before running. Read the two safety
flags first: both start in the safe position.
"""
from dataclasses import dataclass


@dataclass
class LiveConfig:
    # Your paper account id, starts with DU. Required.
    account: str = "DUT139070"
    # Contract ids for the two legs. Find them with find_conids.py, then set here.
    conid_y: int = 1322028   # Safran
    conid_x: int = 14217   # Siemens
    base_ccy: str = "EUR"

    # Safety flags.
    paper_only: bool = True   # refuse to run if the account is not a paper (DU) account
    dry_run: bool = True      # log the orders it would place, place nothing

    # Strategy parameters. The lookback matches the article's formation window.
    lookback: int = 90
    entry_z: float = 2.0
    exit_z: float = 0.5

    # Sizing and risk, in base currency.
    gross_per_leg: float = 10000.0
    max_gross: float = 40000.0
    per_name_cap: float = 25000.0

    # Historical data request to the gateway.
    period: str = "2y"
    bar: str = "1d"

    # Files.
    state_file: str = "live_state.json"
    log_file: str = "live_pairs.log"
