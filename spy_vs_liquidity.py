# import pandas_datareader.data as web
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime

# 1. 设置时间：过去3年 (涵盖熊市到牛市)
start = datetime.datetime(2022, 1, 1)
end = datetime.datetime.now()

print("正在获取数据: SPY vs Tier 1 (WRESBAL)...")

# 2. 获取 Tier 1 数据 (银行准备金) - 使用直接 CSV 下载替代 pandas_datareader
# WRESBAL: 商业银行在美联储的存款 (真正的燃料)
try:
    fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=WRESBAL"
    tier1_data = pd.read_csv(fred_url, index_col=0, parse_dates=True)
    # Filter by date
    tier1_data = tier1_data.loc[start:end]
except Exception as e:
    print(f"Error fetching FRED data: {e}")
    exit(1)

# 3. 获取 SPY 数据 (标普500)
# auto_adjust=True helps with splits/dividends, similar to Adj Close
spy_data = yf.download('SPY', start=start, end=end, auto_adjust=False)

# Handle yfinance multi-index if present, or just grab Adj Close
if isinstance(spy_data.columns, pd.MultiIndex):
    spy = spy_data['Adj Close']
else:
    spy = spy_data['Adj Close']

# 4. 画图：大盘 vs 水位
fig, ax1 = plt.subplots(figsize=(14, 7))

# --- 左轴：Tier 1 (准备金) ---
color1 = '#2ca02c'  # 绿色 (代表资金/安全感)
ax1.set_xlabel('Date')
ax1.set_ylabel('Tier 1 Liquidity (WRESBAL) - Billions $', color=color1, fontsize=12, fontweight='bold')
ax1.plot(tier1_data.index, tier1_data['WRESBAL'], color=color1, linewidth=2.5, label='Tier 1: Bank Reserves')
ax1.tick_params(axis='y', labelcolor=color1)
# 加个网格，方便对齐
ax1.grid(True, alpha=0.3)

# --- 右轴：SPY (标普500) ---
ax2 = ax1.twinx()
color2 = '#8c564b'  # 棕色 (代表传统/稳重)
ax2.set_ylabel('S&P 500 (SPY) Price ($)', color=color2, fontsize=12, fontweight='bold')
ax2.plot(spy.index, spy, color=color2, linewidth=2, linestyle='--', label='SPY Price')
ax2.tick_params(axis='y', labelcolor=color2)

# 标题
plt.title('The "Broad Market" View: SPY vs Tier 1 Liquidity', fontsize=16)
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
fig.tight_layout()

# Save instead of show for headless environment
output_file = 'spy_vs_liquidity.png'
plt.savefig(output_file)
print(f"Chart saved to {output_file}")
