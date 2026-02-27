import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime

# 1. 设置时间：过去3年
start = datetime.datetime(2023, 1, 1)
end = datetime.datetime.now()

print("正在获取数据，请稍候...")

# 2. 从 FRED 获取高收益债利差数据
# BAMLH0A0HYM2: ICE BofA US High Yield Index Option-Adjusted Spread
def get_fred_data(series_id):
    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}'
    df = pd.read_csv(url, index_col=0, parse_dates=True)
    return df

try:
    spread_df = get_fred_data('BAMLH0A0HYM2')
    spread = spread_df.loc[start:end]
    spread = spread.ffill()
except Exception as e:
    print(f"Error downloading Spread data: {e}")
    spread = pd.DataFrame()

# 3. 获取 QQQ 价格
try:
    qqq_df = yf.download('QQQ', start=start, end=end, auto_adjust=True)
    # Handle multi-index columns if present (common in recent yfinance)
    if isinstance(qqq_df.columns, pd.MultiIndex):
        qqq = qqq_df.xs('Close', axis=1, level=0).iloc[:, 0]
    elif 'Close' in qqq_df.columns:
        qqq = qqq_df['Close']
    else:
        qqq = qqq_df.iloc[:, 0]
except Exception as e:
    print(f"Error downloading QQQ: {e}")
    qqq = pd.Series()

# 4. 画图：相关性视角
if not spread.empty and not qqq.empty:
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # 左轴：高收益债利差 (逆序显示，因为利差越低越好，倒过来和股价相关性更直观)
    color1 = 'tab:red'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('High Yield Spread (%) - Inverted', color=color1, fontsize=12)
    ax1.plot(spread.index, spread['BAMLH0A0HYM2'], color=color1, linewidth=2, label='HY Spread (Inverted)')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    # 关键点：倒序Y轴
    ax1.invert_yaxis()
    ax1.grid(True, alpha=0.3)

    # 右轴：QQQ (蓝色)
    ax2 = ax1.twinx()
    color2 = 'tab:blue'
    ax2.set_ylabel('QQQ Price ($)', color=color2, fontsize=12)
    ax2.plot(qqq.index, qqq, color=color2, linewidth=2, linestyle='-', label='QQQ Price')
    ax2.tick_params(axis='y', labelcolor=color2)

    plt.title('Risk Appetite: HY Spread vs Nasdaq 100', fontsize=16)
    
    # 添加图例
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    fig.tight_layout()
    plt.savefig('spread_vs_qqq.png')
    print("图表已保存为 spread_vs_qqq.png")
else:
    print("数据不足，无法绘图")
