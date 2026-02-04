import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime

# 1. 设置时间：过去5年
start = datetime.datetime.now() - datetime.timedelta(days=365*5)
end = datetime.datetime.now()

print("正在拉取数据，观看'猫鼠游戏'...")

# 2. 获取数据
# WTREGEN: TGA账户 (单位: 十亿) - 每周更新
# Replaced pandas_datareader with direct CSV fetch
url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=WTREGEN'
tga = pd.read_csv(url, index_col=0, parse_dates=True)
tga = tga.loc[start:end]

# QQQ: 纳斯达克100
# Robust yfinance access
try:
    qqq_df = yf.download('QQQ', start=start, end=end, auto_adjust=True)
    if 'Close' in qqq_df.columns:
         qqq = qqq_df['Close']
    else:
         # Fallback for MultiIndex or other
         qqq = qqq_df.iloc[:, 0]
except Exception as e:
    print(f"Error downloading QQQ: {e}")
    qqq = pd.Series()

# 3. 画图：双轴叠加
fig, ax1 = plt.subplots(figsize=(14, 7))

# --- 左轴：TGA (红色 - 代表吸血/危险) ---
# 注意：我们要把 TGA 画成"反向"吗？不，直接画，看负相关更直观。
color1 = '#d62728' # Red
ax1.set_xlabel('Date')
ax1.set_ylabel('Treasury General Account (TGA) - Billions $', color=color1, fontsize=12, fontweight='bold')
ax1.plot(tga.index, tga['WTREGEN'], color=color1, linewidth=2, label='TGA (Gov Cash)')
ax1.tick_params(axis='y', labelcolor=color1)
# 给 TGA 区域涂色，增加压迫感
ax1.fill_between(tga.index, tga['WTREGEN'], color=color1, alpha=0.1)

# --- 右轴：QQQ (蓝色 - 代表股市) ---
ax2 = ax1.twinx()
color2 = '#1f77b4' # Blue
ax2.set_ylabel('QQQ Price ($)', color=color2, fontsize=12, fontweight='bold')
ax2.plot(qqq.index, qqq, color=color2, linewidth=2, linestyle='-', label='QQQ Price')
ax2.tick_params(axis='y', labelcolor=color2)

# 标题
plt.title('The "Cat & Mouse" Game: TGA vs QQQ (Last 5 Years)', fontsize=16)
plt.grid(True, alpha=0.3)

# 增加注释：解释相关性
# Position text relative to axes to avoid data overlap if possible, or keep simple
try:
    mid_date = start + (end-start)/2
    qqq_mean = float(qqq.mean()) if not qqq.empty else 0
    text_kwargs = dict(ha='center', va='center', fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8))
    plt.text(mid_date, qqq_mean, "Watch for Inverse Correlation:\nTGA Up (Drain) -> QQQ Stress\nTGA Down (Inject) -> QQQ Boost", **text_kwargs)
except:
    pass # Skip text if calculations fail

fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
fig.tight_layout()

# plt.show()
plt.savefig('tga_vs_qqq.png')
print("图表已保存为 tga_vs_qqq.png")
