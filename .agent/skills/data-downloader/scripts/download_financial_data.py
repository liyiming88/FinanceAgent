#!/usr/bin/env python3
"""
Financial Data Downloader — 项目唯一数据下载入口
Part of the data-downloader Agent Skill

支持两种模式:
  analysis  — 为 balanced-finance-analyst / macro-finance-analyst 下载最近 3 个月宏观指标
  backtest  — 为 Backtest Agent 下载 10 年历史数据

Usage:
  python download_financial_data.py --mode analysis           # 分析数据
  python download_financial_data.py --mode analysis --force   # 强制覆盖
  python download_financial_data.py --mode backtest           # 回测数据
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# =============================================================================
# Project Root (auto-detect: 4 levels up from this script)
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[4]

# =============================================================================
# Analysis-mode Configuration
# =============================================================================

ANALYSIS_FRED_SERIES = {
    # --- Weekly Fed & Treasury ---
    "WALCL": "美联储总资产 (Fed Total Assets)",
    "WTREGEN": "财政部TGA账户 (Treasury General Account)",
    "WRESBAL": "银行准备金余额 (Reserve Balances)",
    # --- Daily Money Market ---
    "RRPONTSYD": "隔夜逆回购余额 (Overnight Reverse Repo)",
    # --- Monthly Indicators ---
    "BUSLOANS": "商业和工业贷款 (Business Loans)",
    "M2SL": "M2货币供应量 (M2 Money Supply)",
    # --- Daily Rates & Market ---
    "T10Y2Y": "10Y-2Y收益率曲线 (Yield Curve Spread)",
    "DGS2": "2年期国债收益率 (2-Year Treasury Yield)",
    "BAMLC0A0CM": "企业债利差 (Corporate Bond Spread)",
    "BAMLH0A0HYM2": "高收益债利差 (High Yield Bond Spread)",
    "T10YIE": "10年期通胀预期 (10Y Breakeven Inflation)",
    "DTWEXBGS": "美元指数-广义 (Broad Dollar Index DXY)",
    "DCOILWTICO": "WTI原油价格 (WTI Crude Oil Price)",
}

QRA_URL = "https://home.treasury.gov/policy-issues/financing-the-government/quarterly-refunding"

# =============================================================================
# Backtest-mode Configuration (参照 download_eval_data.py)
# =============================================================================

BACKTEST_SOURCES = {
    # 'Output_Filename': ('source_type', 'ticker')
    "QQQ.csv": ("yahoo", "QQQ"),
    "SHV.csv": ("yahoo", "SHV"),
    "WRESBAL.csv": ("fred", "WRESBAL"),
    "WTREGEN.csv": ("fred", "WTREGEN"),
    "RRPONTSYD.csv": ("fred", "RRPONTSYD"),
    "BAMLH0A0HYM2.csv": ("fred", "BAMLH0A0HYM2"),
    "PCEPI.csv": ("fred", "PCEPI"),
}

BACKTEST_YEARS = 10


# =============================================================================
# Shared Utility Functions
# =============================================================================


def trim_to_recent_25_percent(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the most recent 25% of data points (≈3 months from 1yr)."""
    if len(df) == 0:
        return df
    rows_to_keep = max(1, len(df) // 4)
    return df.tail(rows_to_keep).reset_index(drop=True)


def fetch_fred_series_raw(series_id: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Fetch a single FRED series as DataFrame (raw, no trimming).
    Returns DataFrame with Date and Value columns.
    """
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
        return df

    except Exception as e:
        print(f"  ❌ Error fetching {series_id}: {e}")
        return pd.DataFrame(columns=["Date", "Value"])


def fetch_yahoo_ticker_raw(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Fetch a Yahoo Finance ticker as DataFrame (raw, no trimming).
    Returns DataFrame with Date and OHLCV columns (index=Date).
    """
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df = df.xs(ticker, level=1, axis=1)
            except KeyError:
                pass
        return df
    except Exception as e:
        print(f"  ❌ Error fetching {ticker}: {e}")
        return pd.DataFrame()


def fetch_yahoo_close(ticker: str, symbol_name: str, start_date: datetime, end_date: datetime, trim: bool = False) -> pd.DataFrame:
    """
    Fetch Yahoo Finance close prices and return a Date / Value DataFrame.
    Optionally trims to recent 25%.
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(start=start_date.strftime("%Y-%m-%d"),
                         end=end_date.strftime("%Y-%m-%d"))
        if len(hist) == 0:
            print(f"  ⚠️ {symbol_name}: No data")
            return pd.DataFrame(columns=["Date", "Value"])

        df = hist.reset_index()[["Date", "Close"]].copy()
        df.columns = ["Date", "Value"]
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
        df = df.dropna()

        if trim:
            df = trim_to_recent_25_percent(df)

        return df
    except Exception as e:
        print(f"  ❌ Error fetching {symbol_name}: {e}")
        return pd.DataFrame(columns=["Date", "Value"])


# =============================================================================
# Analysis Mode — Download Functions
# =============================================================================


def download_analysis_fred(years: int = 1) -> dict[str, pd.DataFrame]:
    """Download all analysis FRED series (trimmed to recent 25%)."""
    results = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)

    print("\n📊 Downloading FRED Data (Analysis)...")
    print("-" * 50)

    for series_id, description in ANALYSIS_FRED_SERIES.items():
        print(f"  ⏳ {series_id}: {description}...", end=" ")
        df = fetch_fred_series_raw(series_id, start_date, end_date)

        if len(df) > 0:
            df = trim_to_recent_25_percent(df)
            print(f"✅ {len(df)} data points")
            results[series_id] = df
        else:
            print("⚠️ No data")

    return results


def fetch_qra_announcements() -> pd.DataFrame:
    """Fetch Treasury Quarterly Refunding Announcement links."""
    print("\n📋 Fetching Treasury QRA Announcements...")
    print("-" * 50)

    try:
        response = requests.get(QRA_URL, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        qra_data = []
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if any(kw in text.lower() for kw in ["refunding", "financing", "borrowing"]):
                if any(kw in href.lower() for kw in [".pdf", "announcement", "statement"]):
                    full_url = href if href.startswith("http") else f"https://home.treasury.gov{href}"
                    qra_data.append({
                        "Title": text[:100],
                        "URL": full_url,
                        "Type": "PDF" if ".pdf" in href.lower() else "Webpage"
                    })

        df = pd.DataFrame(qra_data).drop_duplicates(subset=["URL"]).head(12)

        if len(df) > 0:
            print(f"  ✅ Found {len(df)} QRA-related documents")
        else:
            df = pd.DataFrame([
                {
                    "Title": "Treasury Quarterly Refunding Page",
                    "URL": QRA_URL,
                    "Type": "Main Page"
                },
            ])
            print("  ⚠️ Using fallback links")

        return df

    except Exception as e:
        print(f"  ❌ Error fetching QRA: {e}")
        return pd.DataFrame([
            {"Title": "Treasury Quarterly Refunding (Manual Access)", "URL": QRA_URL, "Type": "Main Page"}
        ])


def fetch_qqq_weekly_ma20() -> pd.DataFrame:
    """
    Fetch QQQ weekly data, calculate MA20, and return the most recent 30 weeks.
    Provides Date, Close, MA20, and Value (same as Close for compatibility).
    """
    try:
        t = yf.Ticker("QQQ")
        # 需获取过去2年周线数据以确保MA20准确
        hist = t.history(period="2y", interval="1wk", auto_adjust=True)
        if len(hist) == 0:
            print("  ⚠️ QQQ: No weekly data")
            return pd.DataFrame(columns=["Date", "Close", "MA20", "Value"])

        hist["MA20"] = hist["Close"].rolling(window=20).mean()
        df = hist.reset_index()[["Date", "Close", "MA20"]].copy()
        df["Value"] = df["Close"] # 为了兼容其它的 summary 逻辑
        df.columns = ["Date", "Close", "MA20", "Value"]
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        cols = ['Close', 'MA20', 'Value']
        df[cols] = df[cols].round(2)
        df = df.dropna()

        # 保留最近 30 周的数据
        return df.tail(30).reset_index(drop=True)[["Date", "Close", "MA20", "Value"]]
    except Exception as e:
        print(f"  ❌ Error fetching QQQ weekly: {e}")
        return pd.DataFrame(columns=["Date", "Close", "MA20", "Value"])


def download_analysis_yahoo(years: int = 1) -> dict[str, pd.DataFrame]:
    """Download MOVE, Copper, Gold, QQQ MA20 from Yahoo Finance (trimmed)."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    results = {}

    print("\n📈 Fetching Yahoo Finance Data (Analysis)...")
    print("-" * 50)

    # MOVE Index
    print("  ⏳ MOVE Index (^MOVE)...", end=" ")
    move_df = fetch_yahoo_close("^MOVE", "MOVE", start_date, end_date, trim=True)
    if len(move_df) > 0:
        print(f"✅ {len(move_df)} data points")
        results["MOVE"] = move_df
    else:
        print("⚠️ No data")

    # QQQ Weekly MA20
    print("  ⏳ QQQ Weekly MA20...", end=" ")
    qqq_df = fetch_qqq_weekly_ma20()
    if len(qqq_df) > 0:
        print(f"✅ {len(qqq_df)} data points")
        results["QQQ_MA20"] = qqq_df
    else:
        print("⚠️ No data")

    # Copper (HG=F)
    print("  ⏳ Copper (HG=F)...", end=" ")
    copper_df = fetch_yahoo_close("HG=F", "COPPER", start_date, end_date, trim=True)
    if len(copper_df) > 0:
        print(f"✅ {len(copper_df)} data points")
        results["COPPER"] = copper_df
    else:
        print("⚠️ No data")

    # Gold (GC=F)
    print("  ⏳ Gold (GC=F)...", end=" ")
    gold_df = fetch_yahoo_close("GC=F", "GOLD", start_date, end_date, trim=True)
    if len(gold_df) > 0:
        print(f"✅ {len(gold_df)} data points")
        results["GOLD"] = gold_df
    else:
        print("⚠️ No data")

    # Copper/Gold Ratio (calculated)
    if "COPPER" in results and "GOLD" in results:
        print("  ⏳ Calculating Copper/Gold Ratio...", end=" ")
        try:
            merged = pd.merge(results["COPPER"], results["GOLD"], on="Date", suffixes=("_copper", "_gold"))
            merged["Value"] = merged["Value_copper"] / merged["Value_gold"]
            ratio_df = merged[["Date", "Value"]].dropna()
            if len(ratio_df) > 0:
                print(f"✅ {len(ratio_df)} data points")
                results["COPPER_GOLD_RATIO"] = ratio_df
        except Exception as e:
            print(f"❌ Error: {e}")

    return results


def export_analysis_csv(
    fred_data: dict[str, pd.DataFrame],
    qra_data: pd.DataFrame,
    yahoo_data: dict[str, pd.DataFrame],
    output_path: str,
) -> str:
    """Export all analysis data to individual CSV files."""
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

    # Yahoo data files (MOVE, COPPER, GOLD, COPPER_GOLD_RATIO)
    for name, df in yahoo_data.items():
        if len(df) > 0:
            filepath = os.path.join(output_path, f"{name}.csv")
            print(f"  📄 Writing {name}.csv...")
            df.to_csv(filepath, index=False)
            exported_files.append(filepath)

    # Summary file
    print("  📄 Writing Summary.csv...")
    summary_rows = []
    all_data = {**fred_data, **yahoo_data}
    for name, df in all_data.items():
        if len(df) > 0:
            summary_rows.append({
                "Series": name,
                "Description": ANALYSIS_FRED_SERIES.get(name, name),
                "Data Points": len(df),
                "Start Date": df["Date"].iloc[0],
                "End Date": df["Date"].iloc[-1],
                "Latest Value": df["Value"].iloc[-1],
            })
    summary_df = pd.DataFrame(summary_rows)
    summary_filepath = os.path.join(output_path, "Summary.csv")
    summary_df.to_csv(summary_filepath, index=False)
    exported_files.append(summary_filepath)

    print(f"\n✅ Successfully exported {len(exported_files)} CSV files to: {output_path}")
    return output_path


# =============================================================================
# Backtest Mode — Download Functions (参照 download_eval_data.py)
# =============================================================================


def download_backtest_data(output_dir: str) -> None:
    """Download 10-year backtest data for all configured tickers."""
    os.makedirs(output_dir, exist_ok=True)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=BACKTEST_YEARS * 365)

    print(f"\n📊 Downloading Backtest Data ({BACKTEST_YEARS} years)...")
    print(f"   Period: {start_date.date()} → {end_date.date()}")
    print("-" * 50)

    for filename, (source, ticker) in BACKTEST_SOURCES.items():
        output_path = os.path.join(output_dir, filename)
        print(f"  ⏳ {ticker} ({source}) → {filename}...", end=" ")

        try:
            df = None

            if source == "yahoo":
                df = fetch_yahoo_ticker_raw(ticker, start_date, end_date)

            elif source == "fred":
                df = fetch_fred_series_raw(ticker, start_date, end_date)
                if len(df) > 0:
                    # Convert to indexed format matching download_eval_data.py output
                    df_out = df.copy()
                    df_out["Date"] = pd.to_datetime(df_out["Date"])
                    df_out.set_index("Date", inplace=True)
                    df_out.index.name = "DATE"
                    df_out.to_csv(output_path)
                    print(f"✅ {len(df_out)} rows")
                    continue

            if df is not None and not df.empty:
                df.to_csv(output_path)
                print(f"✅ {len(df)} rows")
            else:
                print("❌ Empty data")

        except Exception as e:
            print(f"❌ Error: {e}")


# =============================================================================
# Main Entry Point
# =============================================================================


def run_analysis(force: bool = False) -> None:
    """Execute the analysis download pipeline."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = str(PROJECT_ROOT / "datas" / "analysis" / today_str)

    # Dedup check: skip if today's folder already exists
    if os.path.isdir(output_dir) and not force:
        print(f"\n⏭️  今天的数据已存在: {output_dir}")
        print("   如需重新下载，请使用 --force 参数")
        return

    print("=" * 60)
    print("🌐 Financial Data Downloader — Analysis Mode")
    print("=" * 60)
    print(f"📅 Data Range: ~3 months (1yr download, keep recent 25%)")
    print(f"📁 Output: {output_dir}")

    # Download FRED
    fred_data = download_analysis_fred(years=1)

    # Fetch QRA
    qra_data = fetch_qra_announcements()

    # Download Yahoo (MOVE, Copper, Gold, Ratio)
    yahoo_data = download_analysis_yahoo(years=1)

    # Export
    export_analysis_csv(fred_data, qra_data, yahoo_data, output_dir)

    print("\n" + "=" * 60)
    print("📊 Analysis Download Complete!")
    print("=" * 60)
    print(f"📁 Output: {output_dir}")
    print(f"📈 FRED: {len(fred_data)}/{len(ANALYSIS_FRED_SERIES)}")
    print(f"📋 QRA: {len(qra_data)} docs")
    print(f"📊 Yahoo: {len(yahoo_data)} series")
    print()


def run_backtest() -> None:
    """Execute the backtest download pipeline."""
    output_dir = str(PROJECT_ROOT / "datas" / "backtest")

    print("=" * 60)
    print("🌐 Financial Data Downloader — Backtest Mode")
    print("=" * 60)
    print(f"📅 Data Range: {BACKTEST_YEARS} years")
    print(f"📁 Output: {output_dir}")

    download_backtest_data(output_dir)

    print("\n" + "=" * 60)
    print("📊 Backtest Download Complete!")
    print("=" * 60)
    print(f"📁 Output: {output_dir}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Financial Data Downloader — 项目唯一数据下载入口"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["analysis", "backtest"],
        required=True,
        help="Download mode: 'analysis' (3-month macro data) or 'backtest' (10-year history)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        default=False,
        help="Force re-download even if today's data already exists (analysis mode only)"
    )

    args = parser.parse_args()

    if args.mode == "analysis":
        run_analysis(force=args.force)
    elif args.mode == "backtest":
        run_backtest()


if __name__ == "__main__":
    main()
