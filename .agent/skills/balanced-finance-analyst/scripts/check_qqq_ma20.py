#!/usr/bin/env python3
"""
QQQ MA20 状态检查脚本
用于 balanced-finance-analyst skill 的核心数据获取工具

功能：
1. 获取 QQQ 周线数据 (Weekly K-Line) - 过去 2 年
2. 计算 20周均线 (MA20)
3. 输出 CSV 文件 - 仅保存最近 5 周数据 (周K + MA20)
4. 显示当前趋势状态
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys


def get_qqq_data():
    """获取 QQQ 周线数据 (含 MA20)"""
    
    print("正在获取 QQQ 数据...")
    
    try:
        qqq = yf.Ticker("QQQ")
        
        # 1. 获取2年周线数据 (Weekly K-line)
        # auto_adjust=True 保证价格是复权后的真实价格
        hist_weekly = qqq.history(period="2y", interval="1wk", auto_adjust=True)
        
        if hist_weekly.empty:
            print("❌ 获取周线数据失败，请检查网络 (可能需要科学上网)")
            return None
        
        # 2. 计算 20周均线 (MA20)
        hist_weekly['MA20'] = hist_weekly['Close'].rolling(window=20).mean()
        
        # 3. 整理数据
        # 保留 OHLC 和 MA20
        df_result = hist_weekly[['Close', 'MA20']].copy()
        
        # 处理日期格式
        df_result.reset_index(inplace=True)
        df_result['Date'] = df_result['Date'].dt.strftime('%Y-%m-%d')
        
        # 舍入小数位
        cols = ['Close', 'MA20']
        df_result[cols] = df_result[cols].round(2)
        
        # Reorder columns explicitly to match user request: Date, Close, MA20
        df_result = df_result[['Date', 'Close', 'MA20']]
        
        return df_result
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        print("💡 提示: 请检查网络连接，可能需要科学上网访问 Yahoo Finance")
        return None



# =============================================================================
# Macro Logic
# =============================================================================

def update_macro_data(output_dir):
    """Call data-downloader to get fresh macro data"""
    print("⏳ 正在更新宏观数据 (运行 data-downloader)...")
    downloader_script = Path(__file__).parent.parent.parent / "data-downloader" / "scripts" / "download_financial_data.py"
    
    if not downloader_script.exists():
        print(f"⚠️ 找不到下载器脚本: {downloader_script}")
        return False
        
    cmd = [
        sys.executable,
        str(downloader_script),
        "--output", str(output_dir),
        "--years", "1"
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ 宏观数据更新完毕")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据更新失败: {e}")
        return False

def get_latest_value(df):
    """Helper to get latest date and value"""
    if df is None or df.empty:
        return None, 0
    row = df.iloc[-1]
    return row['Date'], float(row['Value'])

def get_prev_value(df, steps=1):
    """Helper to get previous value (n steps back)"""
    if df is None or len(df) <= steps:
        return 0
    return float(df.iloc[-(steps+1)]['Value'])

def analyze_macro_status(macro_dir):
    """Analyze macro indicators and return status"""
    
    # 1. Read files
    try:
        # tga_df = pd.read_csv(macro_dir / "WTREGEN.csv")      # Not used in Tier 1 logic
        res_df = pd.read_csv(macro_dir / "WRESBAL.csv")      # Millions
        # rrp_df = pd.read_csv(macro_dir / "RRPONTSYD.csv")    # Not used in Tier 1 logic
        hy_df = pd.read_csv(macro_dir / "BAMLH0A0HYM2.csv")  # Percent
        us10y_df = pd.read_csv(macro_dir / "DGS10.csv")      # Percent
    except Exception as e:
        print(f"⚠️ 读取宏观数据失败 (可能文件缺失, 请先运行下载器): {e}")
        return None

    # 2. Extract Latest Values
    res_date, res_val = get_latest_value(res_df)      # Millions
    hy_date, hy_val = get_latest_value(hy_df)         # Percent
    us10y_date, us10y_val = get_latest_value(us10y_df)# Percent
    
    # 3. Extract Previous Values (for trend)
    res_prev = get_prev_value(res_df)
    hy_prev = get_prev_value(hy_df)
    us10y_prev = get_prev_value(us10y_df, 5) # Compare with 1 week ago for "WoW"
    
    # 4. Determine Component Signals
    components = []
    
    # Tier 1 Liquidity (WRESBAL only)
    res_diff = res_val - res_prev
    liq_trend_up = res_diff >= 0
    components.append({
        "Name": "🏦 Tier1 流动性 (Reserves)",
        "Value": f"${res_val/1000:.2f} B",
        "Trend": "⬆️" if res_diff >= 0 else "⬇️",
        "Result": "🟢 充沛" if liq_trend_up else "🔴 紧缩",
        "Principle": "银行手里的真金白银 (越高越好)"
    })
    
    # US10Y (Gravity)
    # Judge: > 3% WoW Jump = Red
    if us10y_prev > 0:
        us10y_change_pct = (us10y_val - us10y_prev) / us10y_prev
    else:
        us10y_change_pct = 0
        
    us10y_spike = us10y_change_pct > 0.03 # >3% jump
    components.append({
        "Name": "🌌 地心引力 (US10Y)",
        "Value": f"{us10y_val:.2f}%",
        "Trend": "⬆️" if us10y_val >= us10y_prev else "⬇️",
        "Result": "🔴 暴涨" if us10y_spike else "🟢 平稳",
        "Principle": "无风险收益率 (暴涨=杀估值)"
    })
    
    # HY Spread (Lower is Good)
    hy_diff = hy_val - hy_prev
    components.append({
        "Name": "⚠️ 高收益债利差 (Spread)",
        "Value": f"{hy_val:.2f}%",
        "Trend": "⬆️" if hy_diff >= 0 else "⬇️",
        "Result": "🔴 恐慌" if hy_val >= 5.0 else "🟢 贪婪",
        "Principle": "市场对垃圾债的风险定价 (越低越好)"
    })

    # 4. Determine Signals
    signals = {
        "Liquidity": {
            "Value": res_val / 1000,
            "Signal": "🟢 充沛" if liq_trend_up else "🔴 紧缩",
            "IsGreen": liq_trend_up
        },
        "US10Y": {
            "Value": us10y_val,
            "Signal": "🔴 暴涨" if us10y_spike else "🟢 平稳",
            "IsGreen": not us10y_spike
        },
        "HY_Spread": {
            "Value": hy_val,
            "Signal": "🟢 稳定" if hy_val < 5.0 else "🔴 恶化",
            "IsGreen": hy_val < 5.0
        },
        "Components": components
    }
    
    return signals


# =============================================================================
# Main Check Logic
# =============================================================================

def check_qqq_ma20_status():
    """检查 QQQ 的 MA20 状态并输出 CSV"""
    
    # --- Step 0: Macro Data Update ---
    script_dir = Path(__file__).parent
    macro_data_dir = script_dir.parents[3] / "datas" / "analysis" / "macro"
    update_macro_data(macro_data_dir)
    
    macro_signals = analyze_macro_status(macro_data_dir)

    # --- Step 1: QQQ Data ---
    df = get_qqq_data()
    if df is None:
        return
    
    # Save CSV
    csv_data = df.tail(5)
    output_dir = script_dir.parents[3] / "datas" / "analysis" / "balanced"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    csv_path = output_dir / f"qqq_ma20_{timestamp}.csv"
    csv_data.to_csv(csv_path, index=False)
    print(f"✅ QQQ数据已保存: {csv_path}")

    # --- Step 2: Technical Analysis ---
    latest = df.iloc[-1]
    current_date = latest['Date']
    current_price = latest['Close']
    current_ma20 = latest['MA20']
    
    if pd.isna(current_ma20):
        print("⚠️ MA20 数据不足")
        return

    buffer_line = current_ma20 * 0.99
    gap_pct = (current_price - current_ma20) / current_ma20 * 100
    
    # Technical Signal
    tech_signal_green = current_price > current_ma20
    trend_desc = "🟢 线上" if tech_signal_green else "🔴 线下"
    if gap_pct < 0 and gap_pct > -1: trend_desc = "🟡 缓冲区"
    
    # --- Step 3: Combined Report ---
    print("\n" + "=" * 60)
    print("🛡️ BALANCED STRATEGY MONITOR (Combined)")
    print("=" * 60)
    
    print(f"[1] 核心技术面 (Technical): {current_date}")
    print(f"  📏 QQQ 价格      : ${current_price:.2f}")
    print(f"  🛑 20周均线      : ${current_ma20:.2f}")
    print(f"  📐 距离均线      : {gap_pct:+.2f}%")
    print(f"  🚦 技术信号      : {trend_desc}")
    
    if macro_signals:
        liq = macro_signals["Liquidity"]
        hy = macro_signals["HY_Spread"]
        us10y = macro_signals["US10Y"]
        
        print(f"\n[2] 宏观面 (Macro Integration):")
        
        print(f"\n  | 核心指标 | 最新数值 | 趋势 | 判定结果 | 原理逻辑 |")
        print(f"  |:---|:---|:---|:---|:---|")
        for c in macro_signals["Components"]:
             print(f"  | {c['Name']} | {c['Value']} | {c['Trend']} | {c['Result']} | {c['Principle']} |")

        # Summary line using new simplified logic
        print(f"\n  🌊 Tier1 流动性: [{liq['Signal']}]   *(公式: WRESBAL)*")
        print(f"  🌌 地心引力:   [{us10y['Signal']}]   *(US10Y > 3% WoW)*")
        print(f"  🌡️ 风险情绪:   [{hy['Signal']}]      *(阈值: 利差 > 5%)*")
        
        # Final Advice Logic
        print("-" * 60)
        
        # Determine DCA Advice
        # Logic: 
        # - Red Light (Gap < -1%) or Buffer (-1 <= Gap < 0): QQQ $0, All to SGOV.
        # - Green Light (Gap >= 3%) or Trial (0 <= Gap < 3%): QQQ $Half.
        
        # Re-eval Technical Status for DCA
        # We need precise Gap% logic from SKILL.md
        # Gap < 0: NO QQQ.
        # Gap >= 0: YES QQQ.
        # Wait, SKILL.md says: 
        # Gap < -1%: Red (0% QQQ)
        # -1% <= Gap < 0%: Yellow (Holder Hold / Buyer 0%) -> FOR BUYER NO QQQ.
        # 0 <= Gap < 3%: Yellow (Trial 25%) -> Suggest Buy ($500 -> 50%? No, 25% allocation means half of monthly budget? 
        # The DCA Calculator example says: "若 🟡 试探期 或 🟢 安全区: 预算的 50% (例如 $100)."
        # So if Gap >= 0, we buy QQQ. If Gap < 0, we don't.
        
        dca_budget = 200 # Example
        sgov_amt = dca_budget / 2 # Fixed 50%
        qqq_amt = 0
        qqq_action_msg = "🚫 禁止买入 (转投 SGOV)"
        
        if gap_pct >= 0:
            qqq_amt = dca_budget / 2
            qqq_action_msg = f"✅ 买入 ${qqq_amt:.0f}"
            
        print("[3] 账户配置建议 (Allocation):")
        print(f"  🔒 稳健底仓 (SGOV) : 50%  [雷打不动]")
        print(f"  ⚔️ 进攻仓位 (QQQ)  : {'0% (防御中)' if gap_pct < 0 else ('25% (试探)' if gap_pct < 3 else '50% (满仓)')}")
        print("  -----------------------------------------")
        print("  💵 本周定投指令 (Weekly DCA Action):")
        print("  -----------------------------------------")
        print(f"  本周预算: ${dca_budget} (示例)")
        print(f"  1. SGOV 买入: ${sgov_amt + (qqq_amt if qqq_amt==0 else 0):.0f} (含转移资金)" if qqq_amt==0 else f"  1. SGOV 买入: ${sgov_amt:.0f}")
        print(f"  2. QQQ  买入: ${qqq_amt:.0f} ({qqq_action_msg})")
        
        # 🟢 全绿灯 Logic
        # New Rule: Tier1 Green AND Risk Green AND Price Green.
        # Note: US10Y is monitoring, but user said "Should not determine empty position alone, but guide timing".
        # But user also said "Macro Filter Table... Red Light Decision".
        # If US10Y is Red, does it block "Full Green"?
        # The "Combined Traffic Light" section in SKILL.md says:
        # "Includes ANY Red Light: ... Price Red -> Empty. Risk Red -> Empty. Liquidity Red -> Reduce."
        # It doesn't explicitly mention US10Y in the "Combined Traffic Light" logic section in the updated SKILL.md (I updated the table but not the text below it extensively, assuming the table drives the logic).
        # Let's assume if US10Y is Red (Spike), it's a warning but maybe not a hard block for "Green Light" unless specified. 
        # Actually user said: "⬆️ 暴涨 (>3% WoW): 🔴 杀估值预警 (定投建议推迟到周一尾盘)"
        # So it affects TIMING, not necessarily the Go/No Go for the week's strategic stance, but "Red Light" usually means caution.
        # Let's count it as a warning factor.
        
        is_all_green = tech_signal_green and liq['IsGreen'] and hy['IsGreen'] and us10y['IsGreen']
        
        print("  -----------------------------------------")
        if is_all_green:
            final_verdict = "🟢 全绿灯: 满仓进攻 (50% QQQ + 50% SGOV)"
        else:
            reasons = []
            if not tech_signal_green: reasons.append("价格线下")
            if not liq['IsGreen']: reasons.append("Tier1流出")
            if not hy['IsGreen']: reasons.append("利差恐慌")
            if not us10y['IsGreen']: reasons.append("美债杀估值")
            
            final_verdict = f"⚠️ 警戒模式 ({', '.join(reasons)})"
            
            if not hy['IsGreen'] or not tech_signal_green:
                final_verdict += "\n👉 建议: 强制空仓 QQQ (0%)"
            elif not liq['IsGreen']:
                final_verdict += "\n👉 建议: 降仓至 25% 或 观望"
            elif not us10y['IsGreen']:
                final_verdict += "\n👉 建议: 暂缓买入，周一尾盘再看"
                
        print(f"⚖️ 最终决策建议: \n{final_verdict}")

    print("-" * 60)
    print("\n📄 最近 5 周数据预览:")
    print(csv_data.to_string(index=False))
    
    return df


if __name__ == "__main__":
    try:
        check_qqq_ma20_status()
    except Exception as e:
        print(f"程序出错: {e}")
