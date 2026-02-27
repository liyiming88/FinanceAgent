import os
import datetime
import pandas as pd
import yfinance as yf

# Setup directory
DATA_DIR = "/Users/patrick_0000/develop/AIPOC/FinanceAgent/eval/datas"
os.makedirs(DATA_DIR, exist_ok=True)

# Define date range
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365 * 12)  # 12 years buffer

print(f"Downloading data from {start_date.date()} to {end_date.date()}...")

# 1. Download QQQ from Yahoo Finance
print("Downloading QQQ...")
try:
    qqq = yf.download("QQQ", start=start_date, end=end_date, progress=False)
    # Handle multi-index if present
    if isinstance(qqq.columns, pd.MultiIndex):
        # We prefer 'Close'
        try:
            qqq = qqq['Close']
        except KeyError:
            # Fallback if structure is different
            qqq = qqq.xs('Close', level=0, axis=1)
    
    # Ensure it's a Series or DataFrame with one column
    if isinstance(qqq, pd.DataFrame) and qqq.shape[1] > 1:
        # If still multiple columns, try to pick the one named 'QQQ'
        if 'QQQ' in qqq.columns:
            qqq = qqq[['QQQ']]
        else:
             # Just take the first column as fallback
            qqq = qqq.iloc[:, 0]
            
    # Rename Series to QQQ if needed for consistency when saving
    if isinstance(qqq, pd.Series):
        qqq.name = "QQQ"

    qqq.to_csv(os.path.join(DATA_DIR, "QQQ.csv"))
    print("QQQ saved.")
except Exception as e:
    print(f"Failed to download QQQ: {e}")

# 2. Download FRED Data directly
fred_tickers = ['WALCL', 'WTREGEN', 'RRPONTSYD', 'WRESBAL', 'PCEPI']
print(f"Downloading FRED data: {fred_tickers}...")

for ticker in fred_tickers:
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ticker}"
        print(f"Fetching {ticker} from {url}...")
        df = pd.read_csv(url, index_col=0, parse_dates=True)
        # Filter by date locally
        df = df[df.index >= start_date]
        df.to_csv(os.path.join(DATA_DIR, f"{ticker}.csv"))
        print(f"{ticker} saved.")
    except Exception as e:
        print(f"Failed to download {ticker}: {e}")

print("Download complete.")
