import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import datetime

# 1. 设置短线时间窗口：过去 6个月 (Short-term Focus)
start = datetime.datetime.now() - datetime.timedelta(days=180)
end = datetime.datetime.now()

print("正在拉取短线战术数据...")

# 2. 获取数据
# ^TNX: 10年期美债收益率
# QQQ: 纳指100
# QQQE: 纳指100等权重
tickers = ['QQQ', '^TNX', 'QQQE']
try:
    # Use auto_adjust=True for better data quality (Splits/Dividends handled)
    # This usually returns 'Close' instead of 'Adj Close'
    raw_data = yf.download(tickers, start=start, end=end, auto_adjust=True)
    
    # Check if we have a MultiIndex with 'Close'
    if isinstance(raw_data.columns, pd.MultiIndex):
        if 'Close' in raw_data.columns.get_level_values(0):
             data = raw_data['Close']
        else:
             # Fallback: maybe just take the first level if structure is weird
             data = raw_data.iloc[:, 0] # Risky but fallback
    else:
        # If single level, maybe it's just the tickers (if only 1 ticker) or just prices?
        # With multiple tickers, it should be MultiIndex (Price, Ticker) or (Ticker, Price)
        # Recent yfinance often puts Price on level 0.
        if 'Close' in raw_data.columns:
            data = raw_data['Close']
        else:
            data = raw_data # Hope for the best
            
except Exception as e:
    print(f"Error downloading data: {e}")
    data = pd.DataFrame()

# Verify we have the columns
missing_cols = [t for t in tickers if t not in data.columns]
if missing_cols:
    print(f"Warning: Missing columns {missing_cols}. Attempting download without auto_adjust...")
    # Fallback to standard download if implicit 'Close' extraction failed
    data = yf.download(tickers, start=start, end=end)['Adj Close']

# 3. 画图
fig, (ax1, ax3) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# --- 图 1: 地心引力 (QQQ vs US10Y) ---
try:
    color_qqq = '#1f77b4' # Blue
    ax1.set_ylabel('QQQ Price ($)', color=color_qqq, fontweight='bold')
    ax1.plot(data.index, data['QQQ'], color=color_qqq, linewidth=2, label='QQQ')
    ax1.tick_params(axis='y', labelcolor=color_qqq)
    ax1.grid(True, alpha=0.3)

    # 右轴：10年期收益率 (注意：我们把它 INVERT 倒过来画！)
    ax2 = ax1.twinx()
    color_yield = '#d62728' # Red
    ax2.set_ylabel('US 10Y Yield (Inverted)', color=color_yield, fontweight='bold')
    # invert_yaxis() 让收益率越高，线越往下。这样方便看正相关性。
    ax2.plot(data.index, data['^TNX'], color=color_yield, linewidth=1.5, linestyle='--', label='10Y Yield (Inverted)')
    ax2.tick_params(axis='y', labelcolor=color_yield)
    ax2.invert_yaxis() 

    ax1.set_title('Weapon #1: Gravity - QQQ vs Inverted 10Y Yield\n(Gap = Opportunity)', fontsize=12)

    # --- 图 2: 谎言检测 (QQQ vs QQQE) ---
    ax3.set_ylabel('Price ($)', fontweight='bold')
    # 归一化 (Normalize) 到起点为 100，方便对比涨幅差异
    norm_qqq = data['QQQ'] / data['QQQ'].iloc[0] * 100
    norm_qqqe = data['QQQE'] / data['QQQE'].iloc[0] * 100

    ax3.plot(data.index, norm_qqq, color=color_qqq, linewidth=2, label='QQQ (Market Cap Weight)')
    ax3.plot(data.index, norm_qqqe, color='green', linewidth=2, linestyle='--', label='QQQE (Equal Weight)')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    ax3.set_title('Weapon #2: The Lie Detector - QQQ vs Equal Weight\n(Divergence = Weakness)', fontsize=12)

    plt.tight_layout()
    # plt.show()
    plt.savefig('gravity_lie_detector.png')
    print("图表已保存为 gravity_lie_detector.png")

except KeyError as e:
    print(f"Data missing for plotting: {e}")
    print("Available columns:", data.columns)
except Exception as e:
    print(f"An error occurred during plotting: {e}")
