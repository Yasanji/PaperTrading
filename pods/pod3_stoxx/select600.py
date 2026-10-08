"""STOXX Europe 600 selection: every stock ranked 1-550 is in; remaining places go to current members ranked 551-750
in rank order, then to the highest-ranked non-members. Returns the selected set as a boolean Series."""
import pandas as pd
def select(rank, member, n=600, top=550, keep=750):
    sel = rank <= top
    pool = rank[member & ~sel & (rank <= keep)].sort_values()
    sel.loc[pool.index[:max(0, n - sel.sum())]] = True
    if sel.sum() < n: sel.loc[rank[~sel].sort_values().index[:n - sel.sum()]] = True
    return sel
