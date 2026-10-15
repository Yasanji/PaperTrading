#!/bin/sh
# Build the SSRN PDF: figures from ../fig1_lp.csv and ../fig2_rolling.csv, then pandoc -> xelatex.
set -e
cd "$(dirname "$0")"
python3 make_figs.py
pandoc paper.md -s -H head.tex -o p.tex
sed -i '/lmodern/d' p.tex
xelatex -interaction=nonstopmode p.tex >/dev/null; xelatex -interaction=nonstopmode p.tex >/dev/null
mv p.pdf Ratnaike_Rebalancing_Canada_Australia_SSRN.pdf
