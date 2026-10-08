"""Shared settings for the daily trading job. Every number here comes from book/PORTFOLIO_PREREGISTRATION.md."""
import math, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DB = os.environ.get('DELTA1_DB', os.path.join(ROOT, 'delta1', 'delta1.db'))
NAV = 1_000_000                 # s.1.2; replaced by the previous close's NAV once the book trades
BOOK_VOL = 0.06                 # s.3.1
VOL_WINDOW = 126                # s.3.1
N_PODS = 6
POD_RISK = NAV * BOOK_VOL / math.sqrt(N_PODS)          # as in contract_check.py
SCALE = {1: 1.0, 2: 0.25, 3: 0.25, 4: 0.25, 5: 0.25, 6: 0.25}   # s.6.4 incubation / forward test; pod 1 at 1.0 in paper (BOOK_AMENDMENT_1)
TREND_SHARE, CARRY_SHARE = 0.75, 0.25                  # s.2
MIN_HOLD_DAYS = 15              # s.3.6
NO_TRADE_BAND = 0.25            # s.3.7
ORDER_LIMIT = 0.10              # s.3.4 and DESIGN s.6.4: one order <= 10% of NAV
DAILY_LIMIT = 0.50              # DESIGN s.6.4
PRICE_SANITY = 0.10             # DESIGN s.6.5
ROLL_BDAYS = 5                  # s.7.3
PAPER_PORT = 4002               # IB Gateway paper port
ACCOUNT_FILE = os.path.expanduser('~/.delta1/paper_account')
CONTRACTS = os.path.join(ROOT, 'book', 'contract_check_2026-10-06.csv')
TARGETS_DIR = os.path.join(ROOT, 'book', 'targets')
ORDERS_DIR = os.path.join(ROOT, 'book', 'orders')
