"""Bring the brokerage (iserver) session online and poll until it is ready."""
import time
from ibkr import IBKR

ib = IBKR()
for i in range(12):
    try:
        ib.tickle()
    except Exception as e:
        print(f"[{i}] tickle error: {e}")
    try:
        ib.reinit()
        init = "ok"
    except Exception as e:
        init = f"error: {e}"
    try:
        st = ib.auth_status() or {}
    except Exception as e:
        st = {"error": str(e)}
    print(f"[{i}] init={init} authenticated={st.get('authenticated')} "
          f"connected={st.get('connected')} competing={st.get('competing')}")
    if st.get("authenticated") and st.get("connected"):
        print("SESSION READY")
        break
    time.sleep(3)
else:
    print("Session did not come up. See notes.")
