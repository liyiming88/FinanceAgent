import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime

# 1. 设置时间：过去3年
start = datetime.datetime(2023, 1, 1)
end = datetime.datetime.now()

print("正在获取数据，请稍候...")

# 2. 从 FRED 获取数据
# WALCL: 美联储总资产
# WTREGEN: TGA
# RRPONTSYD: 逆回购
def get_fred_data(series_id):
    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}'
    df = pd.read_csv(url, index_col=0, parse_dates=True)
    return df

fred_dfs = []
for series in ['WALCL', 'WTREGEN', 'RRPONTSYD']:
    df = get_fred_data(series)
    fred_dfs.append(df)

fred_data = pd.concat(fred_dfs, axis=1)
fred_data = fred_data.loc[start:end]
fred_data = fred_data.ffill()

# 3. 计算净流动性 (Net Liquidity)
# 公式: Fed Assets - TGA - RRP
# 注意单位换算: WALCL / 1000
fred_data['Net_Liquidity'] = (fred_data['WALCL'] / 1000) - fred_data['WTREGEN'] - fred_data['RRPONTSYD']

# 4. 获取 QQQ 价格
# yfinance output format varies. Using auto_adjust=True usually gives 'Close' as adjusted close.
try:
    qqq_df = yf.download('QQQ', start=start, end=end, auto_adjust=True)
    if 'Close' in qqq_df.columns:
         qqq = qqq_df['Close']
    else:
         # Fallback for MultiIndex or other
         qqq = qqq_df.iloc[:, 0] # Assume first column is close-ish if structure is weird
except Exception as e:
    print(f"Error downloading QQQ: {e}")
    # Create empty series to prevent crash
    qqq = pd.Series()

# 5. 画图：上帝视角
fig, ax1 = plt.subplots(figsize=(14, 7))

# 左轴：流动性 (蓝色)
color1 = 'tab:blue'
ax1.set_xlabel('Date')
ax1.set_ylabel('Net Liquidity (Billions $)', color=color1, fontsize=12)
ax1.plot(fred_data.index, fred_data['Net_Liquidity'], color=color1, linewidth=2, label='Net Liquidity')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)

# 右轴：QQQ (橙色)
ax2 = ax1.twinx()
color2 = 'tab:orange'
ax2.set_ylabel('QQQ Price ($)', color=color2, fontsize=12)
ax2.plot(qqq.index, qqq, color=color2, linewidth=2, linestyle='--', label='QQQ Price')
ax2.tick_params(axis='y', labelcolor=color2)

plt.title('The "God View": Macro Liquidity vs Nasdaq 100', fontsize=16)
fig.tight_layout()
# plt.show() # Changed to savefig to view in the agent environment
plt.savefig('liquidity_vs_qqq.png')
print("图表已保存为 liquidity_vs_qqq.png")
