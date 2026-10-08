import yfinance as yf
def info(isin):
    try:
        i = yf.Ticker(isin).info
        return dict(isin=isin, symbol=i.get('symbol'), mcap=i.get('marketCap'), y_ccy=i.get('currency'), fin_ccy=i.get('financialCurrency'),
                    float_shares=i.get('floatShares'), shares=i.get('sharesOutstanding'), implied_shares=i.get('impliedSharesOutstanding'),
                    price=i.get('currentPrice') or i.get('regularMarketPrice') or i.get('previousClose'), adv3m=i.get('averageDailyVolume3Month'),
                    y_country=i.get('country'), exch=i.get('exchange'))
    except Exception as e:
        return dict(isin=isin, error=str(e)[:200])

