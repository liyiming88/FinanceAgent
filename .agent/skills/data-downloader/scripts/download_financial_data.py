#!/usr/bin/env python3
"""
国际金融数据一键下载器 (Financial Data Downloader)
Part of the data-downloader Agent Skill

Downloads 1-year data for key macro liquidity indicators, but only keeps the
most recent 25% of data points (approximately 3 months).

Supported data sources:
- FRED series (13 indicators)
- Treasury QRA announcements
- MOVE index from Yahoo Finance
- Copper, Gold prices and Copper/Gold ratio
"""

import argparse
import os
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# =============================================================================
# Configuration
# =============================================================================

FRED_SERIES = {
    "WALCL": "美联储总资产 (Fed Total Assets)",
    "WTREGEN": "财政部TGA账户 (Treasury General Account)",
    "RRPONTSYD": "隔夜逆回购余额 (Overnight Reverse Repo)",
    "WRESBAL": "银行准备金余额 (Reserve Balances)",
    "BUSLOANS": "商业和工业贷款 (Business Loans)",
    "M2SL": "M2货币供应量 (M2 Money Supply)",
    "T10Y2Y": "10Y-2Y收益率曲线 (Yield Curve Spread)",
    "DGS2": "2年期国债收益率 (2-Year Treasury Yield)",
    "DGS10": "10年期国债收益率 (10-Year Treasury Yield)",
    "BAMLC0A0CM": "企业债利差 (Corporate Bond Spread)",
    "BAMLH0A0HYM2": "高收益债利差 (High Yield Bond Spread)",
    "T10YIE": "10年期通胀预期 (10Y Breakeven Inflation)",
    "DTWEXBGS": "美元指数-广义 (Broad Dollar Index DXY)",
    "DCOILWTICO": "WTI原油价格 (WTI Crude Oil Price)",
}

QRA_URL = "https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding"

# Default output path (relative to skill directory)
DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "macro-finance-analyst", "finance-data"
)

# =============================================================================
# Utility Functions
# =============================================================================


def trim_to_recent_25_percent(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the most recent 25% of data points.
    
    Args:
        df: DataFrame with time series data (must have 'Date' column)
        
    Returns:
        DataFrame with only the most recent 25% of rows
    """
    if len(df) == 0:
        return df
    
    # Calculate how many rows to keep (25% of total)
    rows_to_keep = max(1, len(df) // 4)
    
    # Keep the last N rows (most recent data)
    return df.tail(rows_to_keep).reset_index(drop=True)


# =============================================================================
# FRED Data Download Module
# =============================================================================


def fetch_fred_series(series_id: str, years: int = 1, trim: bool = True) -> pd.DataFrame:
    """
    Fetch a single FRED series as DataFrame.
    
    Args:
        series_id: FRED series ID (e.g., 'WALCL')
        years: Number of years of data to fetch
        trim: If True, keep only the most recent 25% of data
        
    Returns:
        DataFrame with Date and Value columns (trimmed to recent 25% by default)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
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
        df.columns = ["Date", "Value"]
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
        df = df.dropna()
        
        # Trim to recent 25% if requested
        if trim:
            df = trim_to_recent_25_percent(df)
        
        return df
        
    except Exception as e:
        print(f"  ❌ Error fetching {series_id}: {e}")
        return pd.DataFrame(columns=["Date", "Value"])


def download_all_fred_series(years: int = 1) -> dict[str, pd.DataFrame]:
    """
    Download all FRED series.
    
    Returns:
        Dictionary mapping series ID to DataFrame
    """
    results = {}
    
    print("\n📊 Downloading FRED Data...")
    print("-" * 50)
    
    for series_id, description in FRED_SERIES.items():
        print(f"  ⏳ {series_id}: {description}...", end=" ")
        df = fetch_fred_series(series_id, years)
        
        if len(df) > 0:
            print(f"✅ {len(df)} data points")
            results[series_id] = df
        else:
            print("⚠️ No data")
    
    return results


# =============================================================================
# Treasury QRA Module
# =============================================================================


def fetch_qra_announcements() -> pd.DataFrame:
    """
    Fetch Treasury Quarterly Refunding Announcement links.
    
    Returns:
        DataFrame with QRA information
    """
    print("\n📋 Fetching Treasury QRA Announcements...")
    print("-" * 50)
    
    try:
        response = requests.get(QRA_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find QRA-related links
        qra_data = []
        
        # Look for announcement sections
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            # Filter for QRA-related PDFs and announcements
            if any(keyword in text.lower() for keyword in ["refunding", "financing", "borrowing"]):
                if any(keyword in href.lower() for keyword in [".pdf", "announcement", "statement"]):
                    full_url = href if href.startswith("http") else f"https://home.treasury.gov{href}"
                    qra_data.append({
                        "Title": text[:100],  # Truncate long titles
                        "URL": full_url,
                        "Type": "PDF" if ".pdf" in href.lower() else "Webpage"
                    })
        
        # Remove duplicates and limit to recent
        df = pd.DataFrame(qra_data).drop_duplicates(subset=["URL"]).head(12)
        
        if len(df) > 0:
            print(f"  ✅ Found {len(df)} QRA-related documents")
        else:
            # Fallback with direct links
            df = pd.DataFrame([
                {
                    "Title": "Treasury Quarterly Refunding Page",
                    "URL": QRA_URL,
                    "Type": "Main Page"
                },
                {
                    "Title": "Treasury Borrowing Advisory Committee (TBAC)",
                    "URL": "https://home.treasury.gov/policy-issues/financing-the-government/treasury-borrowing-advisory-committee",
                    "Type": "Webpage"
                }
            ])
            print("  ⚠️ Using fallback links (page structure may have changed)")
        
        return df
        
    except Exception as e:
        print(f"  ❌ Error fetching QRA: {e}")
        return pd.DataFrame([
            {
                "Title": "Treasury Quarterly Refunding (Manual Access)",
                "URL": QRA_URL,
                "Type": "Main Page"
            }
        ])


# =============================================================================
# MOVE Index Guidance
# =============================================================================


def fetch_move_index(years: int = 1, trim: bool = True) -> pd.DataFrame:
    """
    Fetch MOVE index from Yahoo Finance.
    
    Args:
        years: Number of years of data to fetch
        trim: If True, keep only the most recent 25% of data
        
    Returns:
        DataFrame with Date and Value columns (trimmed to recent 25% by default)
    """
    print("\n📈 Fetching MOVE Index from Yahoo Finance...")
    print("-" * 50)
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        # Download MOVE index data (^MOVE)
        ticker = yf.Ticker("^MOVE")
        df = ticker.history(start=start_date.strftime('%Y-%m-%d'), 
                           end=end_date.strftime('%Y-%m-%d'))
        
        if len(df) > 0:
            # Format the data
            df = df.reset_index()
            df = df[["Date", "Close"]].copy()
            df.columns = ["Date", "Value"]
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
            df = df.dropna()
            
            # Trim to recent 25% if requested
            if trim:
                df = trim_to_recent_25_percent(df)
            
            print(f"  ✅ MOVE Index: {len(df)} data points (recent 25%)")
            return df
        else:
            print("  ⚠️ No MOVE data available")
            return pd.DataFrame(columns=["Date", "Value"])
            
    except Exception as e:
        print(f"  ❌ Error fetching MOVE: {e}")
        return pd.DataFrame(columns=["Date", "Value"])


def fetch_copper_gold_ratio(years: int = 1, trim: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fetch Copper and Gold futures prices from Yahoo Finance and calculate ratio.
    
    Args:
        years: Number of years of data to fetch
        trim: If True, keep only the most recent 25% of data
        
    Returns:
        Tuple of (copper_df, gold_df, ratio_df) - each trimmed to recent 25% by default
    """
    print("\n⚖️ Fetching Copper/Gold Ratio from Yahoo Finance...")
    print("-" * 50)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    copper_df = pd.DataFrame(columns=["Date", "Value"])
    gold_df = pd.DataFrame(columns=["Date", "Value"])
    ratio_df = pd.DataFrame(columns=["Date", "Value"])
    
    try:
        # Download Copper futures (HG=F)
        print("  ⏳ Fetching Copper (HG=F)...", end=" ")
        copper_ticker = yf.Ticker("HG=F")
        copper_hist = copper_ticker.history(start=start_date.strftime('%Y-%m-%d'),
                                            end=end_date.strftime('%Y-%m-%d'))
        if len(copper_hist) > 0:
            copper_df = copper_hist.reset_index()[["Date", "Close"]].copy()
            copper_df.columns = ["Date", "Value"]
            copper_df["Date"] = pd.to_datetime(copper_df["Date"]).dt.strftime("%Y-%m-%d")
            copper_df["Value"] = pd.to_numeric(copper_df["Value"], errors="coerce")
            copper_df = copper_df.dropna()
            if trim:
                copper_df = trim_to_recent_25_percent(copper_df)
            print(f"✅ {len(copper_df)} data points (recent 25%)")
        else:
            print("⚠️ No data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    try:
        # Download Gold futures (GC=F)
        print("  ⏳ Fetching Gold (GC=F)...", end=" ")
        gold_ticker = yf.Ticker("GC=F")
        gold_hist = gold_ticker.history(start=start_date.strftime('%Y-%m-%d'),
                                        end=end_date.strftime('%Y-%m-%d'))
        if len(gold_hist) > 0:
            gold_df = gold_hist.reset_index()[["Date", "Close"]].copy()
            gold_df.columns = ["Date", "Value"]
            gold_df["Date"] = pd.to_datetime(gold_df["Date"]).dt.strftime("%Y-%m-%d")
            gold_df["Value"] = pd.to_numeric(gold_df["Value"], errors="coerce")
            gold_df = gold_df.dropna()
            if trim:
                gold_df = trim_to_recent_25_percent(gold_df)
            print(f"✅ {len(gold_df)} data points (recent 25%)")
        else:
            print("⚠️ No data")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Calculate Copper/Gold Ratio
    if len(copper_df) > 0 and len(gold_df) > 0:
        print("  ⏳ Calculating Copper/Gold Ratio...", end=" ")
        try:
            # Merge on date
            merged = pd.merge(copper_df, gold_df, on="Date", suffixes=("_copper", "_gold"))
            merged["Ratio"] = merged["Value_copper"] / merged["Value_gold"]
            ratio_df = merged[["Date", "Ratio"]].copy()
            ratio_df.columns = ["Date", "Value"]
            ratio_df = ratio_df.dropna()
            if trim:
                ratio_df = trim_to_recent_25_percent(ratio_df)
            print(f"✅ {len(ratio_df)} data points (recent 25%)")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return copper_df, gold_df, ratio_df


# =============================================================================
# CSV Export
# =============================================================================


def export_to_csv(
    fred_data: dict[str, pd.DataFrame],
    qra_data: pd.DataFrame,
    move_data: pd.DataFrame,
    copper_data: pd.DataFrame,
    gold_data: pd.DataFrame,
    copper_gold_ratio: pd.DataFrame,
    output_path: str
) -> str:
    """
    Export all data to individual CSV files.
    
    Args:
        fred_data: Dictionary of FRED DataFrames
        qra_data: QRA information DataFrame
        move_data: MOVE index DataFrame
        output_path: Output directory path
        
    Returns:
        Path to the output directory
    """
    os.makedirs(output_path, exist_ok=True)
    
    print(f"\n💾 Exporting to CSV files: {output_path}")
    print("-" * 50)
    
    exported_files = []
    
    # FRED data files
    for series_id, df in fred_data.items():
        filepath = os.path.join(output_path, f"{series_id}.csv")
        print(f"  📄 Writing {series_id}.csv...")
        df.to_csv(filepath, index=False)
        exported_files.append(filepath)
    
    # QRA file
    qra_filepath = os.path.join(output_path, "QRA_Info.csv")
    print("  📄 Writing QRA_Info.csv...")
    qra_data.to_csv(qra_filepath, index=False)
    exported_files.append(qra_filepath)
    
    # MOVE file
    if len(move_data) > 0:
        move_filepath = os.path.join(output_path, "MOVE.csv")
        print("  📄 Writing MOVE.csv...")
        move_data.to_csv(move_filepath, index=False)
        exported_files.append(move_filepath)
    
    # Copper file
    if len(copper_data) > 0:
        copper_filepath = os.path.join(output_path, "COPPER.csv")
        print("  📄 Writing COPPER.csv...")
        copper_data.to_csv(copper_filepath, index=False)
        exported_files.append(copper_filepath)
    
    # Gold file
    if len(gold_data) > 0:
        gold_filepath = os.path.join(output_path, "GOLD.csv")
        print("  📄 Writing GOLD.csv...")
        gold_data.to_csv(gold_filepath, index=False)
        exported_files.append(gold_filepath)
    
    # Copper/Gold Ratio file
    if len(copper_gold_ratio) > 0:
        ratio_filepath = os.path.join(output_path, "COPPER_GOLD_RATIO.csv")
        print("  📄 Writing COPPER_GOLD_RATIO.csv...")
        copper_gold_ratio.to_csv(ratio_filepath, index=False)
        exported_files.append(ratio_filepath)
    
    # Summary file
    print("  📄 Writing Summary.csv...")
    summary_data = []
    for series_id, df in fred_data.items():
        if len(df) > 0:
            summary_data.append({
                "Series": series_id,
                "Description": FRED_SERIES.get(series_id, ""),
                "Data Points": len(df),
                "Start Date": df["Date"].iloc[0],
                "End Date": df["Date"].iloc[-1],
                "Latest Value": df["Value"].iloc[-1] if len(df) > 0 else None
            })
    
    summary_df = pd.DataFrame(summary_data)
    summary_filepath = os.path.join(output_path, "Summary.csv")
    summary_df.to_csv(summary_filepath, index=False)
    exported_files.append(summary_filepath)
    
    print(f"\n✅ Successfully exported {len(exported_files)} CSV files to: {output_path}")
    return output_path


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Download 1-year international financial data to CSV files"
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory path (default: macro-finance-analyst/finance-data)"
    )
    parser.add_argument(
        "--years", "-y",
        type=int,
        default=1,
        help="Number of years of data to download (default: 1)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌐 国际金融数据一键下载器")
    print("   Financial Data Downloader")
    print("=" * 60)
    print(f"📅 Download Period: {args.years} year(s) (keeping recent 25%)")
    print(f"📁 Output Directory: {args.output}")
    
    # Download FRED data (including DXY and WTI Oil)
    fred_data = download_all_fred_series(years=args.years)
    
    # Fetch QRA announcements
    qra_data = fetch_qra_announcements()
    
    # Fetch MOVE index from Yahoo Finance
    move_data = fetch_move_index(years=args.years)
    
    # Fetch Copper, Gold and calculate ratio
    copper_data, gold_data, copper_gold_ratio = fetch_copper_gold_ratio(years=args.years)
    
    # Export to CSV
    output_dir = export_to_csv(
        fred_data, qra_data, move_data,
        copper_data, gold_data, copper_gold_ratio,
        args.output
    )
    
    print("\n" + "=" * 60)
    print("📊 Download Complete!")
    print("=" * 60)
    print(f"\n📁 Output Directory: {output_dir}")
    print(f"📈 FRED Series Downloaded: {len(fred_data)}/{len(FRED_SERIES)}")
    print(f"📋 QRA Documents Found: {len(qra_data)}")
    print(f"📊 MOVE Index Data Points: {len(move_data)}")
    print(f"🥇 Copper/Gold Ratio Data Points: {len(copper_gold_ratio)}")
    print()


if __name__ == "__main__":
    main()
