import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import os
import xlsxwriter

# ==========================================
# ⚙️ 1. GOLBAL CONFIGURATION
# ==========================================
CONFIG = {
    # Fund Setting
    'INITIAL_CASH': 0,           # Initial Cash (Reset every period)
    'WEEKLY_BUDGET': 1000,       # Weekly Investment
    
    # Strategy Parameters
    'MA_WINDOW': 20,             # Moving Average Window
    'CRASH_THRESHOLD': -0.15,    # Drawdown threshold for Kraken mode
    'SLIPPAGE': 0.0005,          # Simulation Slippage
    'RATE_SHOCK_THRESHOLD': 0.20,# Rate MoM Threshold (20%)
    'RATE_MOM_WINDOW': 40,       # Rate Momentum Window (40 days)
    
    # Allocation Weights
    'ALLOC_BULL': {'QQQ': 0.80, 'SGOV': 0.20},
    'ALLOC_BEAR': {'QQQ': 0.20, 'SGOV': 0.80},
    
    # Backtest Periods
    'PERIODS': [
        ('2006-2007', '2006-01-01', '2007-01-01'),
        ('2007-2008', '2007-01-01', '2008-01-01'),
        ('2008-2009', '2008-01-01', '2009-01-01'),
        ('2009-2010', '2009-01-01', '2010-01-01'),
        ('2010-2011', '2010-01-01', '2011-01-01'),
        ('2011-2012', '2011-01-01', '2012-01-01'),
        ('2012-2013', '2012-01-01', '2013-01-01'),
        ('2013-2014', '2013-01-01', '2014-01-01'),
        ('2014-2015', '2014-01-01', '2015-01-01'),
        ('2015-2016', '2015-01-01', '2016-01-01'),
        ('2016-2017', '2016-01-01', '2017-01-01'),
        ('2017-2018', '2017-01-01', '2018-01-01'),
        ('2018-2019', '2018-01-01', '2019-01-01'),
        ('2019-2020', '2019-01-01', '2020-01-01'),
        ('2020-2021', '2020-01-01', '2021-01-01'),
        ('2021-2022', '2021-01-01', '2022-01-01'),
        ('2022-2023', '2022-01-01', '2023-01-01'),
        ('2023-2024', '2023-01-01', '2024-01-01'),
        ('2024-2025', '2024-01-01', '2025-01-01'),
        ('2025-2026', '2025-01-01', '2026-03-01'), 
        ('2006-2026', '2006-01-01', '2026-03-01'), 
    ],
    
    # Output Paths
    'OUTPUT_FILE': 'datas/backtest/Backtest_Report_Batch.xlsx',
    'PLOT_DIR': 'plots'
}

# ==========================================
# 📥 2. DATA LOADING & PRE-PROCESSING
# ==========================================
def load_data():
    """
    Load data from local CSVs (datas/backtest) and calculate technical indicators.
    Enforces using 'Close' price for all calculations and executions.
    """
    print("⏳ Loading Data (from datas/backtest)...")
    start_date = '2005-01-01' 
    data_dir = "datas/backtest" 
    
    # --- Helper: Load from CSV ---
    def load_csv_close(ticker, filename):
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
            
        try:
            df = pd.read_csv(file_path)
            
            # Find Date column (usually first column or named 'Date')
            date_col = 'Date'
            if 'Date' not in df.columns and 'date' in df.columns:
                date_col = 'date'
            elif 'Date' not in df.columns:
                # Assume first column
                date_col = df.columns[0]
                
            # Parse Date
            # Use utc=True to handle potential timezone mixes, then remove timezone
            df[date_col] = pd.to_datetime(df[date_col], utc=True).dt.tz_localize(None).dt.normalize()
            df.set_index(date_col, inplace=True)
            
            # Extract 'Close'
            col_name = 'Close'
            if 'Close' not in df.columns:
                # Try finding a column that looks like Close (e.g. 'close', 'Adj Close' fallback?)
                # For now stick to 'Close' as standard from yfinance/download script
                if 'close' in df.columns:
                    col_name = 'close'
                else:
                    col_name = df.columns[0] # Fallback to first non-date column? Unsafe but maybe needed
            
            series = df[col_name].sort_index()
            
            # Filter by start_date
            series = series[series.index >= pd.to_datetime(start_date)]
            return series
            
        except Exception as e:
            print(f"❌ Error loading {ticker} from {filename}: {e}")
            return None

    # 1. Load Core Assets
    qqq_close = load_csv_close('QQQ', 'QQQ.csv')
    shv_close = load_csv_close('SHV', 'SHV.csv')
    sgov_close = load_csv_close('SGOV', 'SGOV.csv')
    
    # 2. Load Macro Data (US10Y)
    print("⏳ Loading ^TNX (US10Y) data...")
    tnx_close = load_csv_close('^TNX', 'TNX.csv')

    if qqq_close is None:
        raise ValueError("Critical Data Missing: QQQ")

    # 3. Align & Combine SGOV/SHV
    # Logic: Use SGOV if available, fill history with SHV
    # Create Main DataFrame
    data = pd.DataFrame(index=qqq_close.index)
    data['QQQ_Close'] = qqq_close
    
    # Handle Safe Asset
    if shv_close is not None and sgov_close is not None:
         # Combined (SGOV preferred, SHV fallback)
         # Note: combine_first uses the caller's values first. 
         # To prefer SGOV, do sgov.combine_first(shv)
         safe_asset_close = sgov_close.combine_first(shv_close)
    elif shv_close is not None:
        safe_asset_close = shv_close
    elif sgov_close is not None:
        safe_asset_close = sgov_close
    else:
        # Fallback if both missing (shouldn't happen given prior checks)
        safe_asset_close = pd.Series(index=data.index, data=100.0) # Dummy 100? Or fail.
    
    # Align Safe Asset to QQQ
    data['SGOV_Close'] = safe_asset_close
    
    # US10Y
    if tnx_close is not None:
        data['US10Y'] = tnx_close.reindex(data.index).ffill()
    else:
        data['US10Y'] = 0.0 # Should probably warn
        
    # Fill missing values
    data.ffill(inplace=True)
    data.dropna(inplace=True)
    
    # --- Indicator Calculation ---
    
    # 1. MA20 (Trend)
    data['MA20'] = data['QQQ_Close'].rolling(window=CONFIG['MA_WINDOW']).mean()
    
    # 2. Rate Momentum (Shock)
    # 40-period pct change of US10Y Yield
    data['Rate_MOM'] = data['US10Y'].pct_change(periods=CONFIG['RATE_MOM_WINDOW'])
    
    # 3. Reference Signals (Shifted by 1 day to avoid Look-Ahead Bias)
    # We trade on Tuesday Open/Close using Monday's Close signals
    data['Ref_Close']    = data['QQQ_Close'].shift(1)
    data['Ref_MA20']     = data['MA20'].shift(1)
    data['Ref_Rate_MOM'] = data['Rate_MOM'].shift(1)
    
    # 4. Dynamic Drawdown (Kraken Signal)
    # Based on Ref_Close (Yesterday's close)
    data['Rolling_Max'] = data['Ref_Close'].cummax()
    data['Drawdown']    = (data['Ref_Close'] - data['Rolling_Max']) / data['Rolling_Max']
    
    return data

# ==========================================
# 🤖 3. STRATEGY ENGINE
# ==========================================
def run_strategy(df_slice):
    """
    Execute weekly DCA strategy on the given data slice.
    Uses 'Close' price for execution with slippage simulation.
    """
    cash = CONFIG['INITIAL_CASH']
    shares = {'QQQ': 0, 'SGOV': 0}
    history = []
    
    for date, row in df_slice.iterrows():
        # 🗓️ Weekly Trigger: Tuesday Only (Weekday 1)
        if date.weekday() != 1:
            continue
            
        # Data Integrity Check
        if pd.isna(row['Ref_Close']) or pd.isna(row['Ref_MA20']):
            continue

        # --- Signal Context ---
        ref_price    = row['Ref_Close']
        ref_ma20     = row['Ref_MA20']
        drawdown     = row['Drawdown'] 
        ref_rate_mom = row['Ref_Rate_MOM'] if not pd.isna(row['Ref_Rate_MOM']) else 0
        
        # --- Execution Price ---
        # Simulating execution at Close price (or Open if preferred, but user requested consistent Close usage?)
        # User said "All prices use close". So we buy at today's Close.
        # Adding slippage to penalize the buying price
        exec_price_qqq  = row['QQQ_Close'] * (1 + CONFIG['SLIPPAGE'])
        exec_price_sgov = row['SGOV_Close'] * (1 + CONFIG['SLIPPAGE'])
        
        signal_type = "WAIT"
        
        # 1. Inject Capital
        cash += CONFIG['WEEKLY_BUDGET']
        
        buy_qqq_amt = 0
        buy_sgov_amt = 0
        
        # ==========================================
        # 🔥 Priority 0: Rate Shock Meltdown (Defensive)
        # ==========================================
        # Logic: If rates spike > 20% in 40 days -> Valuation Crash -> RISK OFF
        if ref_rate_mom > CONFIG['RATE_SHOCK_THRESHOLD']:
            signal_type = "📉 RATE_SHOCK"
            
            # Action: Liquidate QQQ
            if shares['QQQ'] > 0:
                # Sell QQQ
                qqq_sell_val = shares['QQQ'] * row['QQQ_Close'] # Sell at Close
                cash += qqq_sell_val
                shares['QQQ'] = 0
            
            # Action: All Cash into SGOV
            buy_qqq_amt = 0
            buy_sgov_amt = cash 
            
        # ==========================================
        # 🔥 Priority 1: The Kraken (Crash Buying)
        # ==========================================
        # Logic: If Drawdown < -15% AND No Rate Shock -> Deep Value -> SGOV to QQQ
        elif drawdown < CONFIG['CRASH_THRESHOLD'] and shares['SGOV'] > 0:
            signal_type = "🔥 KRAKEN"
            
            # Action: Sell 50% SGOV to buy QQQ
            sgov_sell_qty = shares['SGOV'] * 0.5
            cash += sgov_sell_qty * row['SGOV_Close']
            shares['SGOV'] -= sgov_sell_qty
            
            buy_qqq_amt = cash # All in to QQQ
            buy_sgov_amt = 0
            
        # ==========================================
        # 🐂 Priority 2: Bull Mode (Ref > MA20)
        # ==========================================
        elif ref_price > ref_ma20:
            signal_type = "BULL"
            buy_qqq_amt = cash * CONFIG['ALLOC_BULL']['QQQ']
            buy_sgov_amt = cash * CONFIG['ALLOC_BULL']['SGOV']
            
        # ==========================================
        # 🐻 Priority 3: Bear Mode (Ref <= MA20)
        # ==========================================
        else:
            signal_type = "BEAR"
            buy_qqq_amt = cash * CONFIG['ALLOC_BEAR']['QQQ']
            buy_sgov_amt = cash * CONFIG['ALLOC_BEAR']['SGOV']
            
        # --- Trade Execution ---
        if buy_qqq_amt > 1:
            shares['QQQ'] += buy_qqq_amt / exec_price_qqq
            cash -= buy_qqq_amt
            
        if buy_sgov_amt > 1:
            shares['SGOV'] += buy_sgov_amt / exec_price_sgov
            cash -= buy_sgov_amt
            
        # --- Daily Record ---
        # Mark to Market at Close
        curr_qqq = shares['QQQ'] * row['QQQ_Close']
        curr_sgov = shares['SGOV'] * row['SGOV_Close']
        total_assets = cash + curr_qqq + curr_sgov
        
        history.append({
            'Date': date,
            'Total_Asset': total_assets,
            'QQQ_Val': curr_qqq,
            'SGOV_Val': curr_sgov,
            'Cash': cash,
            'Signal': signal_type,
            'Drawdown': drawdown,
            'Price': row['QQQ_Close'],
            'MA20': ref_ma20,
            'Rate_MOM': ref_rate_mom
        })

    if not history:
        return pd.DataFrame(), {}
        
    res_df = pd.DataFrame(history).set_index('Date')
    
    # Statistics
    weeks = len(res_df)
    total_invested = CONFIG['INITIAL_CASH'] + (weeks * CONFIG['WEEKLY_BUDGET'])
    final_value = res_df['Total_Asset'].iloc[-1]
    profit = final_value - total_invested
    
    # ROI (Decimal)
    roi = (profit / total_invested) if total_invested > 0 else 0
    max_dd = res_df['Drawdown'].min()
    
    metrics = {
        'Weeks': weeks,
        'Invested': total_invested,
        'Final_Value': final_value,
        'Profit': profit,
        'ROI_Pct': roi,
        'Max_DD_Pct': max_dd
    }
    
    return res_df, metrics

# ==========================================
# 📊 4. VISUALIZATION
# ==========================================
def create_chart(df_res, title, filename):
    plt.figure(figsize=(10, 12)) # Increase height for 4 subplots
    
    # 0. QQQ Price (Top)
    ax0 = plt.subplot(4, 1, 1)
    # Re-plot QQQ Price from the source data (need to pass it or extract it)
    # Since df_res has 'Price' column which is QQQ Close
    ax0.plot(df_res.index, df_res['Price'], color='black', linewidth=1, label='QQQ Price')
    plt.title(title)
    plt.ylabel('QQQ Price')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)

    # 1. Asset Growth (Stacked)
    ax1 = plt.subplot(4, 1, 2, sharex=ax0)
    plt.stackplot(df_res.index, 
                  df_res['SGOV_Val'], df_res['QQQ_Val'], 
                  labels=['SGOV (Safe)', 'QQQ (Risk)'], 
                  colors=['#a8d08d', '#4472c4'], alpha=0.9)
    plt.ylabel('Portfolio Value ($)')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # 2. Drawdown (Red)
    ax2 = plt.subplot(4, 1, 3, sharex=ax0)
    ax2.fill_between(df_res.index, df_res['Drawdown']*100, 0, color='red', alpha=0.3)
    plt.axhline(y=CONFIG['CRASH_THRESHOLD']*100, color='red', linestyle='--', label='Crash Trigger')
    plt.ylabel('Drawdown %')
    plt.legend(loc='lower left')
    plt.grid(True, alpha=0.3)

    # 3. Rate Momentum (Purple)
    ax3 = plt.subplot(4, 1, 4, sharex=ax0)
    if 'Rate_MOM' in df_res.columns:
        ax3.plot(df_res.index, df_res['Rate_MOM'], color='purple', linewidth=1.5, label='10Y Yield Momentum (40d)')
        ax3.axhline(y=CONFIG['RATE_SHOCK_THRESHOLD'], color='purple', linestyle='--', label='Panic Threshold (0.2)')
        
        # Highlight Shock Areas
        shock_mask = df_res['Rate_MOM'] > CONFIG['RATE_SHOCK_THRESHOLD']
        if shock_mask.any():
            ax3.fill_between(df_res.index, df_res['Rate_MOM'], CONFIG['RATE_SHOCK_THRESHOLD'], 
                             where=shock_mask, color='purple', alpha=0.3)
                             
        plt.ylabel('Rate MoM')
        plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# ==========================================
# 🚀 MAIN ENTRY
# ==========================================
if __name__ == "__main__":
    if not os.path.exists(CONFIG['PLOT_DIR']):
        os.makedirs(CONFIG['PLOT_DIR'])
        
    # 1. Load Data
    full_data = load_data()
    if full_data is None:
        exit()
        
    # 2. Init Report
    print(f"📄 Creating Report: {CONFIG['OUTPUT_FILE']} ...")
    writer = pd.ExcelWriter(CONFIG['OUTPUT_FILE'], engine='xlsxwriter')
    workbook = writer.book
    
    summary_data = [] 
    
    # 3. Batch Backtest
    for label, start_dt, end_dt in CONFIG['PERIODS']:
        print(f"👉 Running: {label} [{start_dt} -> {end_dt}]")
        
        # Slice Data
        mask = (full_data.index >= start_dt) & (full_data.index < end_dt)
        sub_df = full_data.loc[mask].copy()
        
        if sub_df.empty:
            print("   ⚠️ Data empty, skipping")
            continue
            
        # Run Strategy
        res_df, metrics = run_strategy(sub_df)
        
        if res_df.empty:
            print("   ⚠️ No trades, skipping")
            continue
            
        # Collect Metrics
        metrics['Period'] = label
        summary_data.append(metrics)
        
        # Draw Chart
        plot_filename = os.path.join(CONFIG['PLOT_DIR'], f"chart_{label}.png")
        plot_title = f"{label} | ROI: {metrics['ROI_Pct']:.2%} | Final: ${metrics['Final_Value']:,.0f}"
        create_chart(res_df, plot_title, plot_filename)
        
        # Write Sheet
        sheet_name = label
        res_df.to_excel(writer, sheet_name=sheet_name, startrow=20)
        
        worksheet = writer.sheets[sheet_name]
        
        # Sheet Header
        bold_fmt = workbook.add_format({'bold': True, 'font_size': 12})
        worksheet.write('A1', f"Period: {label}", bold_fmt)
        worksheet.write('A2', f"ROI: {metrics['ROI_Pct']:.2%}", bold_fmt)
        worksheet.write('A3', f"Profit: ${metrics['Profit']:,.2f}")
        worksheet.write('A4', f"Total Invested: ${metrics['Invested']:,.2f}")
        worksheet.write('A5', f"Final Value: ${metrics['Final_Value']:,.2f}")
        
        # Insert Chart
        worksheet.insert_image('L1', plot_filename, {'x_scale': 0.8, 'y_scale': 0.8})
        
    # 4. Master Summary
    print("📝 Generating Summary...")
    df_summary = pd.DataFrame(summary_data)
    
    if not df_summary.empty:
        # Reorder columns
        cols = ['Period', 'ROI_Pct', 'Profit', 'Final_Value', 'Invested', 'Max_DD_Pct', 'Weeks']
        df_summary = df_summary[cols].copy()
        
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Format Summary
        ws_sum = writer.sheets['Summary']
        pct_fmt = workbook.add_format({'num_format': '0.00%'})
        money_fmt = workbook.add_format({'num_format': '$#,##0.00'})
        
        ws_sum.set_column('A:A', 15)       # Period
        ws_sum.set_column('B:B', 12, pct_fmt) # ROI
        ws_sum.set_column('C:E', 18, money_fmt) # Money
        ws_sum.set_column('F:F', 12, pct_fmt) # Max DD
        
        print("\n" + "="*50)
        print("📊 BACKTEST SUMMARY")
        print("="*50)
        print(df_summary.to_string())
        
    writer.close()
    print(f"\n✅ Done! Report saved to: {CONFIG['OUTPUT_FILE']}")