import os
import yfinance as yf
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta

# Configuration
OUTPUT_DIR = "eval/datas"
YEARS = 10
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=YEARS * 365)

# Ticker Mappings
# Format: 'Output_Filename': ('Source', 'Ticker')
DATA_SOURCES = {
    'QQQ.csv': ('yahoo', 'QQQ'),
    'SHV.csv': ('yahoo', 'SHV'),
    'WRESBAL.csv': ('fred', 'WRESBAL'),
    'WTREGEN.csv': ('fred', 'WTREGEN'),
    'RRPONTSYD.csv': ('fred', 'RRPONTSYD'),
    'BAMLH0A0HYM2.csv': ('fred', 'BAMLH0A0HYM2'),
}

def fetch_fred_series(series_id, start_date, end_date):
    """Fetch FRED data using direct CSV URL, avoiding pandas_datareader issues."""
    url = (
        f"https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}"
        f"&cosd={start_date.strftime('%Y-%m-%d')}"
        f"&coed={end_date.strftime('%Y-%m-%d')}"
    )
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        # Ensure standard usage: index is Date
        # FRED CSVs usually have 'observation_date' as the first column
        if 'observation_date' in df.columns:
            df['DATE'] = pd.to_datetime(df['observation_date'])
            df.drop(columns=['observation_date'], inplace=True)
        elif 'DATE' in df.columns:
             df['DATE'] = pd.to_datetime(df['DATE'])
        
        df.set_index('DATE', inplace=True)
        return df
    except Exception as e:
        print(f"  ❌ Error fetching {series_id} from FRED: {e}")
        return None

def download_data():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    print(f"Downloading {YEARS} years of data (Start: {START_DATE.date()}, End: {END_DATE.date()})...")

    for filename, (source, ticker) in DATA_SOURCES.items():
        output_path = os.path.join(OUTPUT_DIR, filename)
        print(f"Downloading {ticker} from {source} -> {output_path} ...", end=" ")
        
        try:
            df = None
            if source == 'yahoo':
                df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    try:
                        df = df.xs(ticker, level=1, axis=1)
                    except KeyError:
                        pass # Sometimes it might not have the level if single ticker
                
            elif source == 'fred':
                df = fetch_fred_series(ticker, START_DATE, END_DATE)
            
            if df is not None and not df.empty:
                df.to_csv(output_path)
                print(f"✅ Success ({len(df)} rows)")
            else:
                print("❌ Empty data")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    download_data()
