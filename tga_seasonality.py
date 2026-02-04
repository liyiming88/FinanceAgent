import pandas as pd
import matplotlib.pyplot as plt
import datetime
import requests
import io

# 1. 获取过去 10 年的 TGA 数据
# 使用直接 CSV 下载替代 pandas_datareader 以避免库版本问题
start = datetime.datetime.now() - datetime.timedelta(days=365*10)
end = datetime.datetime.now()

print("正在计算 TGA 的季节性规律...")

try:
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=WTREGEN"
    # Download the content
    response = requests.get(url)
    response.raise_for_status()
    
    # Read into pandas
    tga = pd.read_csv(io.StringIO(response.text), index_col=0, parse_dates=True)
    # Filter by date
    tga = tga.loc[start:end]
except Exception as e:
    print(f"Error fetching TGA data: {e}")
    exit(1)

# 2. 计算每周/每月的资金变动 (Flow)
# 变动 = 本周余额 - 上周余额
# 正数 = 吸血 (存钱) -> 对股市不利
tga['Flow'] = tga['WTREGEN'].diff()

# FRED data for WTREGEN is in Billions? Actually let's check unit.
# WTREGEN is "Deposits with Federal Reserve Banks" in Billions of Dollars usually, 
# but let's just stick to the calculation logic.
# Wait, let's verify if WTREGEN is Millions or Billions.
# Ideally we don't change the user's logic too much, but the previous script treated it as Millions?
# Actually, the user's prompt says "Billions $" in the label.
# FRED WTREGEN is Billions of Dollars.

# 3. 按月份分组，看平均值
tga['Month'] = tga.index.month
monthly_seasonality = tga.groupby('Month')['Flow'].mean()

# 4. 画图
fig, ax = plt.subplots(figsize=(12, 6))

# 设置颜色：红色代表吸血(Flow>0)，绿色代表泄洪(Flow<0)
colors = ['red' if x > 0 else 'green' for x in monthly_seasonality]

bars = ax.bar(monthly_seasonality.index, monthly_seasonality, color=colors)

# 装饰
ax.set_title('TGA Seasonality (10-Year Average): When does Yellen Spend?', fontsize=16)
ax.set_xlabel('Month (1=Jan, 12=Dec)', fontsize=12)
ax.set_ylabel('Average TGA Change (Billions $)', fontsize=12)
ax.set_xticks(range(1, 13))
ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
ax.axhline(0, color='black', linewidth=1)

# 添加说明 - prevent hardcoding index access error if data is missing, though unlikely for seasonality
if 4 in monthly_seasonality.index:
    plt.text(4, monthly_seasonality[4] + (5 if monthly_seasonality[4] > 0 else -5), 
             'April Tax Day\n(Huge Drain)', ha='center', color='red', fontweight='bold')
if 2 in monthly_seasonality.index:
    plt.text(2, monthly_seasonality[2] - (5 if monthly_seasonality[2] < 0 else 5), 
             'Tax Refunds\n(Release)', ha='center', color='green', fontweight='bold')

plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()

# Save instead of show
output_file = 'tga_seasonality.png'
plt.savefig(output_file)
print(f"Chart saved to {output_file}")
