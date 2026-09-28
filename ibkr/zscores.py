"""Print recent daily z-scores for the pair, from the live gateway.

Shows how close the spread is to the entry band. Reuses ibkr.py, statarb.py,
data.py and the settings in live_config.py. Marks entries and exits.
"""
from ibkr import IBKR
from statarb import latest_signal
from data import align, closes_from_history
from live_config import LiveConfig

N = 40  # how many recent sessions to show

cfg = LiveConfig()
ib = IBKR()
ib.tickle()
try:
    ib.reinit()
except Exception:
    pass
ib.accounts()

def closes(conid):
    return closes_from_history(ib.history(conid, period=cfg.period, bar=cfg.bar))

dates, y, x = align(closes(cfg.conid_y), closes(cfg.conid_x))
if len(dates) < cfg.lookback + 1:
    raise SystemExit(f"Only {len(dates)} aligned bars; need more than {cfg.lookback}.")

print(f"date                 z       beta    band")
start = max(cfg.lookback + 1, len(dates) - N)
prev = 0
for i in range(start, len(dates) + 1):
    sig = latest_signal(y[:i], x[:i], cfg.lookback, cfg.entry_z, cfg.exit_z, prev)
    prev = sig.target
    band = ""
    if sig.z is not None:
        if abs(sig.z) >= cfg.entry_z:
            band = "ENTRY"
        elif abs(sig.z) <= cfg.exit_z:
            band = "flat zone"
    z = "n/a" if sig.z is None else f"{sig.z:+.2f}"
    print(f"{dates[i-1]:20s} {z:>6}  {sig.beta:5.2f}   {band}")
