import pandas as pd
import os
import argparse
from datetime import datetime

def analyze_hunter_data(data_dir):
    """
    根据 Investment Hunter 策略分析指定目录下的最新金融数据。
    """
    if not os.path.exists(data_dir):
        print(f"Error: 目录 {data_dir} 不存在。")
        return

    # QQQ
    qqq_path = os.path.join(data_dir, 'QQQ_MA20.csv')
    if not os.path.exists(qqq_path):
         print(f"Error: {qqq_path} 不存在。")
         return
         
    qqq = pd.read_csv(qqq_path)
    latest_qqq = qqq.iloc[-1]
    close = latest_qqq['Close']
    ma20 = latest_qqq['MA20']
    gap = (close - ma20) / (ma20 + 1e-9) * 100
    rolling_max = qqq['Close'].max()
    drawdown = (close - rolling_max) / (rolling_max + 1e-9) * 100

    # DGS2 (Rate Shock)
    dgs2_path = os.path.join(data_dir, 'DGS2.csv')
    if not os.path.exists(dgs2_path):
        print(f"Error: {dgs2_path} 不存在。")
        return
        
    dgs2 = pd.read_csv(dgs2_path)
    dgs2['Date'] = pd.to_datetime(dgs2['Date'])
    dgs2 = dgs2.sort_values('Date').dropna()
    latest_dgs2 = dgs2.iloc[-1]['Value']
    
    if len(dgs2) > 40:
        dgs2_40 = dgs2.iloc[-41]['Value']
    else:
        dgs2_40 = dgs2.iloc[0]['Value']
        
    rate_mom = (latest_dgs2 - dgs2_40) / (dgs2_40 + 1e-9) * 100

    def get_macro(filename):
        try:
            df = pd.read_csv(os.path.join(data_dir, filename))
            if 'Value' not in df.columns:
                return 0, '—'
            df['Date'] = pd.to_datetime(df['Date'])
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
            df = df.sort_values('Date').dropna()
            
            if len(df) == 0:
                return 0, '—'
                
            latest = df.iloc[-1]['Value']
            prev = df.iloc[-2]['Value'] if len(df) > 1 else latest
            trend = '⬆️' if latest > prev else '⬇️' if latest < prev else '—'
            return latest, trend
        except Exception as e:
            return 0, '—'

    wresbal_val, wresbal_trend = get_macro('WRESBAL.csv')
    wtregen_val, wtregen_trend = get_macro('WTREGEN.csv')
    rrp_val, rrp_trend = get_macro('RRPONTSYD.csv')
    hy_val, hy_trend = get_macro('BAMLH0A0HYM2.csv')
    
    try:
        move_val, move_trend = get_macro('MOVE.csv')
    except:
        move_val, move_trend = 0, '—'
        
    dxy_val, dxy_trend = get_macro('DTWEXBGS.csv')
    wti_val, wti_trend = get_macro('DCOILWTICO.csv')
    copper_gold_val, copper_gold_trend = get_macro('COPPER_GOLD_RATIO.csv')

    print("==================================================")
    print("🎯 INVESTMENT HUNTER 数据提取")
    print("==================================================")
    print(f"\n[1] 核心信号数据:")
    print(f"  QQQ 收盘价       : ${close:.2f}")
    print(f"  QQQ 20日均线     : ${ma20:.2f}")
    print(f"  距均线距离 (Gap) : {gap:+.2f}%")
    print(f"  历史最高价       : ${rolling_max:.2f}")
    print(f"  最大回撤 (DD)    : {drawdown:.2f}% (如果< -15% 触发 KRAKEN)")
    print(f"  2年期美债 (DGS2) : {latest_dgs2:.4f}")
    print(f"  40日前DGS2       : {dgs2_40:.4f}")
    print(f"  Rate Momentum    : {rate_mom:+.2f}% (如果> 20% 触发 RATE_SHOCK)")
    
    print(f"\n[2] 宏观过滤器:")
    print(f"  银行准备金(WRESBAL) : {wresbal_val:,.2f} M {wresbal_trend}")
    print(f"  TGA账户(WTREGEN)    : {wtregen_val:,.2f} M {wtregen_trend}")
    print(f"  逆回购(RRPONTSYD)   : {rrp_val:.2f} B {rrp_trend}")
    print(f"  高收益债利差(HY)    : {hy_val:.2f}% {hy_trend}")
    print(f"  MOVE指数            : {move_val:.2f} {move_trend}")
    print(f"  美元指数(DXY)       : {dxy_val:.2f} {dxy_trend}")
    print(f"  WTI原油             : ${wti_val:.2f} {wti_trend}")
    print(f"  铜金比              : {copper_gold_val:.6f} {copper_gold_trend}")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='分析 Investment Hunter 需要的市场数据')
    parser.add_argument('--date', type=str, help='指定数据日期文件夹名称，如 "2023-10-25"。如果不指定，将使用 datas/analysis 下最新的日期文件夹。')
    args = parser.parse_args()

    base_dir = '/Users/patrick_0000/develop/AIPOC/FinanceAgent/datas/analysis'
    
    target_dir = None
    if args.date:
        target_dir = os.path.join(base_dir, args.date)
    else:
        # 寻找最新的目录
        try:
             # 获取所有是目录的项，并排除可能存在的非日期格式目录
             dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
             # 只保留符合日期格式(简易判断)的文件夹并排序
             date_dirs = sorted([d for d in dirs if len(d) == 10 and d.count('-') == 2])
             if date_dirs:
                 target_dir = os.path.join(base_dir, date_dirs[-1])
        except Exception as e:
             pass

    if target_dir:
        print(f"读取数据目录: {target_dir}")
        analyze_hunter_data(target_dir)
    else:
         print(f"Error: 无法在 {base_dir} 下找到有效的日期数据目录。")
