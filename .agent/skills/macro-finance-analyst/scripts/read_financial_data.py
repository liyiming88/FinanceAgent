#!/usr/bin/env python3
"""
金融数据读取器 (Financial Data Reader)
Part of the macro-finance-analyst Agent Skill

Reads all CSV files from the finance-data directory and provides structured access
to key macro liquidity indicators for analysis.

Usage:
    # As a script
    python read_financial_data.py

    # As a module
    from read_financial_data import FinancialDataReader
    reader = FinancialDataReader()
    data = reader.load_all()
"""

import os
import sys
from datetime import datetime
from typing import Optional

import pandas as pd

# =============================================================================
# Configuration
# =============================================================================

# Default data directory path (relative to script location)
DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.path.dirname(os.path.abspath(__file__)),
    "../../../../datas/analysis/macro"
)

# FRED series descriptions
FRED_SERIES = {
    "WALCL": "美联储总资产 (Fed Total Assets)",
    "WTREGEN": "财政部TGA账户 (Treasury General Account)",
    "RRPONTSYD": "隔夜逆回购余额 (Overnight Reverse Repo)",
    "WRESBAL": "银行准备金余额 (Reserve Balances)",
    "BUSLOANS": "商业和工业贷款 (Business Loans)",
    "M2SL": "M2货币供应量 (M2 Money Supply)",
    "T10Y2Y": "10Y-2Y收益率曲线 (Yield Curve Spread)",
    "BAMLC0A0CM": "企业债利差 (Corporate Bond Spread)",
    "T10YIE": "10年期通胀预期 (10Y Breakeven Inflation)",
}

# Additional data files
ADDITIONAL_FILES = {
    "MOVE": "债市波动率指数 (MOVE Index)",
    "QRA_Info": "财政部季度再融资公告 (Treasury QRA)",
    "Summary": "数据汇总 (Data Summary)",
}


# =============================================================================
# Financial Data Reader Class
# =============================================================================


class FinancialDataReader:
    """
    Reads and provides structured access to financial data from CSV files.
    """

    def __init__(self, data_dir: str = DEFAULT_DATA_DIR):
        """
        Initialize the reader with the path to the finance-data directory.
        
        Args:
            data_dir: Path to the directory containing CSV files
        """
        self.data_dir = os.path.abspath(data_dir)
        self.data: dict[str, pd.DataFrame] = {}
        self.summary: Optional[pd.DataFrame] = None
        self.qra_info: Optional[pd.DataFrame] = None
        self.move_data: Optional[pd.DataFrame] = None
        self._loaded = False

    def load_all(self) -> dict[str, pd.DataFrame]:
        """
        Load all CSV files from the data directory.
        
        Returns:
            Dictionary mapping file names (without extension) to DataFrames
        """
        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(
                f"Financial data directory not found: {self.data_dir}\n"
                "Please run the data-downloader skill first."
            )

        print(f"📂 Loading data from: {self.data_dir}")
        print("-" * 60)

        # Find all CSV files in the directory
        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            raise FileNotFoundError(
                f"No CSV files found in: {self.data_dir}\n"
                "Please run the data-downloader skill first."
            )

        for csv_file in sorted(csv_files):
            file_path = os.path.join(self.data_dir, csv_file)
            series_name = csv_file.replace('.csv', '')
            
            try:
                df = pd.read_csv(file_path)
                self.data[series_name] = df
                
                # Categorize special files
                if series_name == "Summary":
                    self.summary = df
                elif series_name == "QRA_Info":
                    self.qra_info = df
                elif series_name == "MOVE":
                    self.move_data = df
                
                print(f"  ✅ {series_name}: {len(df)} rows")
            except Exception as e:
                print(f"  ⚠️ {series_name}: Failed to load - {e}")

        self._loaded = True
        print(f"\n📊 Total files loaded: {len(self.data)}")
        return self.data

    def get_series(self, series_id: str) -> Optional[pd.DataFrame]:
        """
        Get a specific FRED series by ID.
        
        Args:
            series_id: FRED series ID (e.g., 'WALCL')
            
        Returns:
            DataFrame with Date and Value columns, or None if not found
        """
        if not self._loaded:
            self.load_all()
        return self.data.get(series_id)

    def get_latest_value(self, series_id: str) -> Optional[tuple[str, float]]:
        """
        Get the latest value for a series.
        
        Args:
            series_id: FRED series ID
            
        Returns:
            Tuple of (date, value) or None if not found
        """
        df = self.get_series(series_id)
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            # Handle different column names (Date/date, Value/value/Close)
            date_col = next((c for c in df.columns if c.lower() == 'date'), df.columns[0])
            value_col = next((c for c in df.columns if c.lower() in ['value', 'close']), df.columns[-1])
            return (str(latest[date_col]), float(latest[value_col]))
        return None

    def get_trend(self, series_id: str, periods: int = 4) -> Optional[str]:
        """
        Determine the recent trend for a series.
        
        Args:
            series_id: FRED series ID
            periods: Number of recent periods to analyze
            
        Returns:
            "UP", "DOWN", or "FLAT"
        """
        df = self.get_series(series_id)
        if df is None or len(df) < periods:
            return None
        
        # Handle different column names
        value_col = next((c for c in df.columns if c.lower() in ['value', 'close']), df.columns[-1])
        recent = df.tail(periods)[value_col]
        change = recent.iloc[-1] - recent.iloc[0]
        pct_change = abs(change) / recent.iloc[0] if recent.iloc[0] != 0 else 0
        
        if pct_change < 0.01:  # Less than 1% change
            return "FLAT"
        return "UP" if change > 0 else "DOWN"

    def print_summary(self):
        """
        Print a formatted summary of all key indicators.
        """
        if not self._loaded:
            self.load_all()

        print("\n" + "=" * 60)
        print("📊 金融数据摘要 (Financial Data Summary)")
        print("=" * 60)
        
        # Print FRED series data
        print("\n### 第一维度：资金源头 ###")
        self._print_indicator("WALCL", "美联储总资产")
        self._print_indicator("WTREGEN", "财政部TGA账户")
        self._print_indicator("RRPONTSYD", "隔夜逆回购余额 (RRP)")
        
        print("\n### 第二维度：传导确认 ###")
        self._print_indicator("WRESBAL", "银行准备金余额")
        self._print_indicator("T10Y2Y", "10Y-2Y收益率曲线")
        
        print("\n### 第三维度：风险定价 ###")
        self._print_indicator("MOVE", "债市波动率指数 (MOVE)")
        self._print_indicator("BAMLC0A0CM", "企业债利差 (HY Spreads)")
        self._print_indicator("T10YIE", "10年期通胀预期")
        
        print("\n### 其他指标 ###")
        self._print_indicator("BUSLOANS", "商业和工业贷款")
        self._print_indicator("M2SL", "M2货币供应量")
        
        # QRA info
        if self.qra_info is not None and len(self.qra_info) > 0:
            print("\n### QRA 公告信息 ###")
            for _, row in self.qra_info.head(3).iterrows():
                title = row.get('Title', row.get('title', 'N/A'))
                if isinstance(title, str):
                    print(f"  📋 {title[:60]}...")
        
        print("\n" + "=" * 60)

    def _print_indicator(self, series_id: str, name: str):
        """Helper to print a single indicator."""
        latest = self.get_latest_value(series_id)
        trend = self.get_trend(series_id)
        
        if latest:
            date, value = latest
            trend_icon = {"UP": "⬆️", "DOWN": "⬇️", "FLAT": "➡️"}.get(trend, "❓")
            print(f"  {trend_icon} {name} ({series_id})")
            print(f"     最新值: {value:,.2f} (日期: {date})")
        else:
            print(f"  ⚠️ {name} ({series_id}): 无数据")

    def get_macro_environment_report(self) -> dict:
        """
        Generate a structured macro environment report for analysis.
        
        Returns:
            Dictionary containing the macro environment assessment
        """
        if not self._loaded:
            self.load_all()

        report = {
            "generated_at": datetime.now().isoformat(),
            "data_source": self.data_dir,
            "indicators": {},
            "assessment": {}
        }

        # Collect indicator data for FRED series
        for series_id in FRED_SERIES.keys():
            latest = self.get_latest_value(series_id)
            trend = self.get_trend(series_id)
            
            if latest:
                report["indicators"][series_id] = {
                    "description": FRED_SERIES[series_id],
                    "latest_date": latest[0],
                    "latest_value": latest[1],
                    "trend": trend
                }

        # Add MOVE index if available
        move_latest = self.get_latest_value("MOVE")
        move_trend = self.get_trend("MOVE")
        if move_latest:
            report["indicators"]["MOVE"] = {
                "description": ADDITIONAL_FILES["MOVE"],
                "latest_date": move_latest[0],
                "latest_value": move_latest[1],
                "trend": move_trend
            }

        # Generate assessment based on key indicators
        walcl_trend = report["indicators"].get("WALCL", {}).get("trend")
        tga_trend = report["indicators"].get("WTREGEN", {}).get("trend")
        reserves_trend = report["indicators"].get("WRESBAL", {}).get("trend")
        
        # Determine cycle
        if walcl_trend == "DOWN":
            report["assessment"]["cycle"] = "缩表 (Contraction)"
            report["assessment"]["risk_level"] = "HIGH"
        elif walcl_trend == "UP":
            report["assessment"]["cycle"] = "扩表 (Expansion)"
            report["assessment"]["risk_level"] = "LOW"
        elif tga_trend == "DOWN" and reserves_trend == "UP":
            report["assessment"]["cycle"] = "财政释放 (Fiscal Release)"
            report["assessment"]["risk_level"] = "MEDIUM"
        else:
            report["assessment"]["cycle"] = "僵持 (Stalemate)"
            report["assessment"]["risk_level"] = "MEDIUM"

        # Check liquidity confirmation
        if tga_trend == "DOWN" and reserves_trend == "UP":
            report["assessment"]["liquidity_confirmed"] = True
            report["assessment"]["liquidity_status"] = "✅ TGA下降且准备金上升，流动性确认有效"
        elif tga_trend == "DOWN" and reserves_trend != "UP":
            report["assessment"]["liquidity_confirmed"] = False
            report["assessment"]["liquidity_status"] = "⚠️ TGA下降但准备金未涨，属于无效释放"
        else:
            report["assessment"]["liquidity_confirmed"] = None
            report["assessment"]["liquidity_status"] = "ℹ️ 等待进一步数据验证"

        # Check MOVE index for risk
        move_value = report["indicators"].get("MOVE", {}).get("latest_value")
        if move_value:
            if move_value > 120:
                report["assessment"]["move_warning"] = "🚨 MOVE指数超过120，债市极度恐慌，禁止开新仓"
            elif move_value > 100:
                report["assessment"]["move_warning"] = "⚠️ MOVE指数偏高，需谨慎操作"
            else:
                report["assessment"]["move_warning"] = "✅ MOVE指数正常"

        return report

    def to_markdown_report(self) -> str:
        """
        Generate a Markdown formatted report of all data.
        
        Returns:
            Markdown string
        """
        report = self.get_macro_environment_report()
        
        md = []
        md.append("# 金融数据分析报告")
        md.append(f"\n**生成时间:** {report['generated_at']}")
        md.append(f"\n**数据来源:** `{report['data_source']}`\n")
        
        md.append("---\n")
        md.append("## 宏观环境评估\n")
        assessment = report.get("assessment", {})
        md.append(f"- **当前周期:** {assessment.get('cycle', 'N/A')}")
        md.append(f"- **风险等级:** {assessment.get('risk_level', 'N/A')}")
        md.append(f"- **流动性状态:** {assessment.get('liquidity_status', 'N/A')}")
        if assessment.get('move_warning'):
            md.append(f"- **MOVE预警:** {assessment.get('move_warning')}\n")
        
        md.append("---\n")
        md.append("## 关键指标详情\n")
        
        for series_id, data in report.get("indicators", {}).items():
            trend_icon = {"UP": "⬆️", "DOWN": "⬇️", "FLAT": "➡️"}.get(data.get("trend"), "❓")
            md.append(f"### {series_id} - {data.get('description', '')}\n")
            md.append(f"- **最新日期:** {data.get('latest_date', 'N/A')}")
            md.append(f"- **最新值:** {data.get('latest_value', 0):,.2f}")
            md.append(f"- **趋势:** {trend_icon} {data.get('trend', 'N/A')}\n")
        
        return "\n".join(md)


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """Main function to demonstrate data reading."""
    print("=" * 60)
    print("🌐 金融数据读取器")
    print("   Financial Data Reader")
    print("=" * 60)
    
    try:
        reader = FinancialDataReader()
        reader.load_all()
        reader.print_summary()
        
        # Generate and display macro report
        print("\n" + "=" * 60)
        print("📋 生成宏观环境报告...")
        print("=" * 60)
        
        report = reader.get_macro_environment_report()
        assessment = report.get("assessment", {})
        
        print(f"\n🔍 当前周期: {assessment.get('cycle', 'N/A')}")
        print(f"⚠️ 风险等级: {assessment.get('risk_level', 'N/A')}")
        print(f"💧 流动性状态: {assessment.get('liquidity_status', 'N/A')}")
        if assessment.get('move_warning'):
            print(f"📊 MOVE预警: {assessment.get('move_warning')}")
        
        print("\n✅ 数据读取完成!")
        
    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("\n💡 请先运行数据下载器:")
        print("   python .agent/skills/data-downloader/scripts/download_financial_data.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
