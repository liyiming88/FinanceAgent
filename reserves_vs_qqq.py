import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime

# 1. 设置时间
start = datetime.datetime(2023, 1, 1)
end = datetime.datetime.now()

print("正在获取纯 Tier 1 数据...")

# 2. 直接获取 WRESBAL (银行准备金 - 真正的燃料)
# 注意：WRESBAL 是周更数据 (每周三)，单位是 Billions (十亿)
# Replaced pandas_datareader with direct CSV fetch to avoid dependency issues
url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=WRESBAL'
tier1_data = pd.read_csv(url, index_col=0, parse_dates=True)
tier1_data = tier1_data.loc[start:end]


# 3. 获取 QQQ 价格
# qqq = yf.download('QQQ', start=start, end=end)['Adj Close']
# Robust yfinance access
try:
    qqq_df = yf.download('QQQ', start=start, end=end, auto_adjust=True)
    if 'Close' in qqq_df.columns:
         qqq = qqq_df['Close']
    else:
         # Fallback for MultiIndex or other structures
         qqq = qqq_df.iloc[:, 0]
except Exception as e:
    print(f"Error downloading QQQ: {e}")
    qqq = pd.Series()

# 4. 画图：燃料 vs 速度
fig, ax1 = plt.subplots(figsize=(14, 7))

# 左轴：银行准备金 (Tier 1 核心)
color1 = '#2ca02c'  # 绿色，代表燃料/安全垫
ax1.set_xlabel('Date')
ax1.set_ylabel('Bank Reserves (WRESBAL) - Billions $', color=color1, fontsize=12, fontweight='bold')
ax1.plot(tier1_data.index, tier1_data['WRESBAL'], color=color1, linewidth=2.5, label='Tier 1: Bank Reserves')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)

# 右轴：QQQ (纳斯达克)
ax2 = ax1.twinx()
color2 = '#1f77b4'  # 蓝色
ax2.set_ylabel('QQQ Price ($)', color=color2, fontsize=12, fontweight='bold')
ax2.plot(qqq.index, qqq, color=color2, linewidth=2, linestyle='--', label='QQQ Price')
ax2.tick_params(axis='y', labelcolor=color2)

# 标题
plt.title('The "Pure" View: Bank Reserves (Tier 1) vs QQQ', fontsize=16)
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
fig.tight_layout()

# plt.show()
plt.savefig('reserves_vs_qqq.png')
print("图表已保存为 reserves_vs_qqq.png")
