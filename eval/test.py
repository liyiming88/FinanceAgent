import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 🛠️ 0. 配置区域 (只需改这里)
# ==========================================
# 文件路径配置 (请确保 CSV 第一列是日期，第二列是数值)
DATA_FILES = {
    'PRICE': 'eval/datas/QQQ.csv',           # QQQ 价格数据 (Yahoo Finance 下载)
    'SAFE':  'eval/datas/SHV.csv',           # SHV 短债数据 (SGOV 历史太短，用 SHV 代替)
    'LIQ_RES': 'eval/datas/WRESBAL.csv',     # 银行准备金 (FRED)
    'LIQ_TGA': 'eval/datas/WTREGEN.csv',     # TGA 账户 (FRED)
    'LIQ_RRP': 'eval/datas/RRPONTSYD.csv',   # 逆回购 (FRED)
    'RISK':    'eval/datas/BAMLH0A0HYM2.csv' # 高收益债利差 (FRED)
}

WEEKLY_BUDGET = 1000  # 每周定投金额
START_DATE = '2021-01-01' # 回测开始时间 (Old config, overridden in main)
END_DATE = '2026-01-01'   # 回测结束时间 (Old config, overridden in main)

# ==========================================
# 📥 1. 数据加载与对齐 (The Data Loader)
# ==========================================
def load_and_merge_data():
    print("正在加载历史数据...")
    df_main = pd.DataFrame()

    # 1. 加载价格数据 (基准)
    # 假设 CSV 格式为: Date, Close
    price_df = pd.read_csv(DATA_FILES['PRICE'], parse_dates=True, index_col=0)
    # 重采样为周五数据 (模拟每周操作一次)
    df_main['QQQ'] = price_df['Close'].resample('W-FRI').last()
    
    # 加载安全资产
    safe_df = pd.read_csv(DATA_FILES['SAFE'], parse_dates=True, index_col=0)
    df_main['SHV'] = safe_df['Close'].resample('W-FRI').last()

    # 2. 加载宏观数据 (并对齐到周五)
    # 注意：FRED 数据通常有延迟，这里我们用 ffill() 模拟"直到本周五能看到的最新数据"
    # 这样就完美实现了你说的"不看未来"
    
    macros = {
        'Reserves': DATA_FILES['LIQ_RES'],
        'TGA': DATA_FILES['LIQ_TGA'],
        'RRP': DATA_FILES['LIQ_RRP'],
        'Spread': DATA_FILES['RISK']
    }
    
    for name, path in macros.items():
        try:
            temp = pd.read_csv(path, parse_dates=True, index_col=0)
            # 这里的列名可能是 VALUE 或其他，统一取第一列
            col_name = temp.columns[0]
            # 转换成数字，处理脏数据
            temp[col_name] = pd.to_numeric(temp[col_name], errors='coerce')
            # 对齐到周五，向前填充 (Forward Fill)
            # 意味着：如果周五没数据，就用周四发布的，绝不用下周一的
            df_main[name] = temp[col_name].resample('W-FRI').last().ffill()
        except Exception as e:
            print(f"⚠️ 警告: 加载 {name} 失败 ({e})，将使用默认值 0")
            df_main[name] = 0

    # 3. 计算技术指标 (MA20)
    # 这可以在循环外算好，因为 MA20 本身就是滞后指标，不存在偷看未来的问题
    df_main['MA20'] = df_main['QQQ'].rolling(window=20).mean()
    
    # 4. 计算流动性指标 (Tier 1)
    # 假设单位不统一，这里做一个粗略的单位对齐 (假设 CSV 里都是 Millions 或 Billions)
    # 建议你在 Excel 里先把单位统一好，或者在这里除以 1000
    df_main['Net_Liquidity'] = df_main['Reserves'] # 简化版：只看准备金趋势
    
    return df_main.dropna()

# ==========================================
# 🧠 2. 逐周回测引擎 (The Simulation Loop)
# ==========================================
def run_simulation(df, start_date, end_date):
    # 开始时间过滤
    df_slice = df[(df.index >= start_date) & (df.index <= end_date)]
    
    print(f"🚀 启动回测... 区间: {start_date} 至 {end_date} (数据行数: {len(df_slice)})")
    
    if len(df_slice) == 0:
        print("⚠️ 警告: 该时间段没有数据！")
        return pd.DataFrame(), pd.DataFrame()

    cash = 0
    holdings = {'QQQ': 0, 'SHV': 0}
    history = []
    investment_log = []

    # --- 核心循环 (你要求的"一段一段喂数据") ---
    # 我们遍历每一行，当程序运行到 `i` 行时，它绝对不知道 `i+1` 行的数据
    
    for date, row in df_slice.iterrows():
        # 1. 每周发工资
        cash += WEEKLY_BUDGET
        
        # 2. 获取"当下"的数据
        price_qqq = row['QQQ']
        price_shv = row['SHV']
        ma20 = row['MA20']
        liquidity = row['Net_Liquidity']
        risk_spread = row['Spread']
        
        # 3. 策略判断逻辑 (The Brain)
        
        # A. 技术面红绿灯
        tech_signal = "GREEN"
        buffer_price = ma20 * 0.99
        if price_qqq < buffer_price:
            tech_signal = "RED"
        elif price_qqq < ma20:
            tech_signal = "YELLOW"
            
        # B. 宏观面红绿灯
        # 规则：利差 > 5% 或者 流动性暴跌
        macro_signal = "NEUTRAL"
        if risk_spread > 5.0:
            macro_signal = "PANIC"
        
        # 4. 执行交易 (Execution)
        
        # --- 场景 1: 止损/避险 (优先级最高) ---
        # 只要技术面破位 OR 宏观恐慌 -> 全部逃跑
        if tech_signal == "RED" or macro_signal == "PANIC":
            # 卖出所有 QQQ
            if holdings['QQQ'] > 0:
                cash += holdings['QQQ'] * price_qqq
                holdings['QQQ'] = 0
            
            # 钱全部买入 SHV (囤子弹)
        
        # --- 场景 2: 资金分配 ---
        alloc_qqq = 0
        alloc_shv = 0
        
        if tech_signal == "RED" or macro_signal == "PANIC":
            # 🔴 全买 SHV
            alloc_shv = cash
        elif tech_signal == "YELLOW":
            # 🟡 观察期: 不买 QQQ，钱存 SHV，但手里的 QQQ 不卖
            alloc_shv = cash
        else:
            # 🟢 绿灯: 真正的 50/50 再平衡
            
            # 1. 第一步：逻辑清空所有持仓，汇聚成大资金池
            current_total_value = cash + (holdings['QQQ'] * price_qqq) + (holdings['SHV'] * price_shv)
            
            # 2. 第二步：重置持仓，重新分配
            holdings['QQQ'] = 0
            holdings['SHV'] = 0
            cash = current_total_value
            
            alloc_qqq = cash * 0.5
            alloc_shv = cash * 0.5
            
        # 执行买入
        if alloc_qqq > 0:
            holdings['QQQ'] += alloc_qqq / price_qqq
            cash -= alloc_qqq
        
        if alloc_shv > 0:
            holdings['SHV'] += alloc_shv / price_shv
            cash -= alloc_shv
            
        # 记录投资明细
        current_step_total = alloc_qqq + alloc_shv
        if current_step_total > 0:
            qqq_ratio = alloc_qqq / current_step_total
            shv_ratio = alloc_shv / current_step_total
        else:
            qqq_ratio = 0
            shv_ratio = 0
            
        investment_log.append({
            'Date': date,
            'QQQ_Price': price_qqq,
            'QQQ_Amount': alloc_qqq,
            'QQQ_Ratio': qqq_ratio,
            'QQQ_Pos_Value': holdings['QQQ'] * price_qqq,
            'SHV_Price': price_shv,
            'SHV_Amount': alloc_shv,
            'SHV_Ratio': shv_ratio,
            'SHV_Pos_Value': holdings['SHV'] * price_shv
        })
            
        # 5. 记录资产快照
        total_val = (holdings['QQQ'] * price_qqq) + (holdings['SHV'] * price_shv) + cash
        history.append({
            'Date': date,
            'Total_Asset': total_val,
            'Signal': tech_signal,
            'Spread': risk_spread,
            'Holdings_QQQ': holdings['QQQ'] * price_qqq,
            'Holdings_SHV': holdings['SHV'] * price_shv,
            'Cash': cash
        })

    return pd.DataFrame(history).set_index('Date'), pd.DataFrame(investment_log).set_index('Date')

# ==========================================
# 📊 3. 运行与绘图
# ==========================================
if __name__ == "__main__":
    try:
        # 1. 准备数据
        full_df = load_and_merge_data()
        
        # 定义要测试的时间段
        periods = [
            ('2017-01-01', '2018-01-01'),
            ('2018-01-01', '2019-01-01'),
            ('2019-01-01', '2020-01-01'),
            ('2020-01-01', '2021-01-01'),
            ('2021-01-01', '2022-01-01'),
            ('2022-01-01', '2023-01-01'),
            ('2023-01-01', '2024-01-01'),
            ('2024-01-01', '2025-01-01'),
            ('2025-01-01', '2026-01-01'),
            ('2017-01-01', '2026-01-01') # 全时段
        ]
        
        summary_results = []
        output_file = 'eval/backtest_results.xlsx'
        
        print(f"📝 准备将结果写入: {output_file}")
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for start_date, end_date in periods:
                sheet_name = f"{start_date[:4]}-{end_date[:4]}"
                print(f"\\n--- 正在测试: {sheet_name} ---")
                
                # 运行回测
                history_df, log_df = run_simulation(full_df, start_date, end_date)
                
                if history_df.empty:
                    print(f"⚠️ {sheet_name} 无数据，跳过")
                    continue
                
                # 计算收益
                total_weeks = len(history_df)
                total_invested = total_weeks * WEEKLY_BUDGET
                final_value = history_df['Total_Asset'].iloc[-1]
                net_profit = final_value - total_invested
                return_rate = (net_profit / total_invested * 100) if total_invested > 0 else 0
                
                print(f"💰 投入: ${total_invested:,.0f} | 💎 最终: ${final_value:,.0f} | 📈 收益率: {return_rate:.2f}%")
                
                # 记录汇总
                summary_results.append({
                    'Period': sheet_name,
                    'Start_Date': start_date,
                    'End_Date': end_date,
                    'Total_Weeks': total_weeks,
                    'Total_Invested': total_invested,
                    'Final_Asset': final_value,
                    'Net_Profit': net_profit,
                    'Return_Rate_Pct': return_rate
                })
                
                # 保存该时段的详细历史到 Sheet
                log_df.to_excel(writer, sheet_name=sheet_name)
            
            # 保存汇总页
            print("\\n📊 正在生成汇总页...")
            summary_df = pd.DataFrame(summary_results)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
        print(f"\\n✅ 所有回测完成！结果已保存至: {output_file}")

    except FileNotFoundError as e:
        print(f"❌ 错误: 找不到 CSV 文件 ({e})。请确保 'data/' 目录下有相关数据。")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ 运行出错: {e}")