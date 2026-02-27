import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# Config
DATA_DIR = "/Users/patrick_0000/develop/AIPOC/FinanceAgent/eval/datas"
OUTPUT_FILE = "trend_plot.png"

def load_data():
    # Load QQQ
    qqq = pd.read_csv(os.path.join(DATA_DIR, "QQQ.csv"), index_col=0, parse_dates=True)
    if 'Close' in qqq.columns:
        qqq = qqq[['Close']]
    qqq.columns = ['QQQ']
    qqq = qqq[~qqq.index.duplicated(keep='first')]
    
    # Load FRED data
    walcl = pd.read_csv(os.path.join(DATA_DIR, "WALCL.csv"), index_col=0, parse_dates=True)
    wtregen = pd.read_csv(os.path.join(DATA_DIR, "WTREGEN.csv"), index_col=0, parse_dates=True)
    rrpontsyd = pd.read_csv(os.path.join(DATA_DIR, "RRPONTSYD.csv"), index_col=0, parse_dates=True)
    wresbal = pd.read_csv(os.path.join(DATA_DIR, "WRESBAL.csv"), index_col=0, parse_dates=True)
    pcepi = pd.read_csv(os.path.join(DATA_DIR, "PCEPI.csv"), index_col=0, parse_dates=True)

    # Rename columns
    walcl.columns = ['WALCL']
    wtregen.columns = ['WTREGEN']
    rrpontsyd.columns = ['RRPONTSYD']
    wresbal.columns = ['WRESBAL']
    pcepi.columns = ['PCEPI']
    
    # Merge
    # Note: PCEPI is monthly, others daily/weekly. Ffill will handle it.
    df = qqq.join([walcl, wtregen, rrpontsyd, wresbal, pcepi], how='outer')
    
    # Forward fill
    df = df.ffill().dropna()
    return df

def plot_trends(df):
    plt.figure(figsize=(14, 8))
    
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
    except:
        plt.style.use('bmh')
    
    fig, ax1 = plt.subplots(figsize=(14, 8))
    fig.subplots_adjust(right=0.85) # Make room for 3rd axis

    # Left Axis: QQQ
    color1 = 'tab:blue'
    ax1.set_xlabel('Date', fontweight='bold')
    ax1.set_ylabel('QQQ Price ($)', color=color1, fontweight='bold')
    ax1.plot(df.index, df['QQQ'], color=color1, label='QQQ Price', linewidth=2)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)

    # Calculate QQQ Growth Multiple (for proportional scaling of PCEPI)
    qqq_min = df['QQQ'].min()
    qqq_max = df['QQQ'].max()
    qqq_ratio = qqq_max / qqq_min
    
    # print(f"QQQ Growth Ratio: {qqq_ratio:.2f}x")

    # Right Axis 1: Liquidity Metrics
    ax2 = ax1.twinx()
    color2_base = 'black'
    ax2.set_ylabel('Liquidity Metrics ($ Billions)', color=color2_base, fontweight='bold')
    
    c1, c2, c3, c4 = 'tab:green', 'tab:orange', 'tab:red', 'tab:purple'
    
    ax2.plot(df.index, df['WALCL'] / 1000, color=c1, label='Fed Bal. Sheet (WALCL)', linestyle='--', alpha=0.6)
    ax2.plot(df.index, df['WTREGEN'] / 1000, color=c2, label='TGA (WTREGEN)', linestyle='-.', alpha=0.6)
    ax2.plot(df.index, df['RRPONTSYD'], color=c3, label='Reverse Repo (RRPONTSYD)', linestyle=':', alpha=0.6)
    ax2.plot(df.index, df['WRESBAL'] / 1000, color=c4, label='Bank Reserves (WRESBAL)', linestyle='-', alpha=0.6, linewidth=1.5)

    ax2.tick_params(axis='y', labelcolor=color2_base)
    
    # Right Axis 2: PCEPI
    ax3 = ax1.twinx()
    # Offset the right spine of ax3. The ticks and label have already been placed on the right by twinx()
    ax3.spines.right.set_position(("axes", 1.08))
    
    color_pce = 'tab:brown'
    ax3.set_ylabel('PCEPI (Index 2017=100)', color=color_pce, fontweight='bold')
    ax3.plot(df.index, df['PCEPI'], color=color_pce, label='PCEPI', linewidth=2.5, linestyle='-')
    ax3.tick_params(axis='y', labelcolor=color_pce)
    
    # --- AUTO-SCALE FIX FOR PCEPI ---
    # To make PCEPI slope look "realistic" relative to QQQ:
    # Set PCEPI Y-Axis range so that the visible height represents the same % growth as QQQ.
    # Logic: QQQ Top / QQQ Bottom = Ratio (e.g. 5x)
    # So PCEPI Axis Top should be approx PCEPI Axis Bottom * Ratio.
    # We take the actual min of PCEPI as the bottom (or slightly lower for padding).
    
    pce_min = df['PCEPI'].min()
    pce_max_actual = df['PCEPI'].max()
    
    # Set lower bound slightly below min
    pce_axis_min = pce_min * 0.95
    # Set upper bound such that (Max / Min) == qqq_ratio
    # Or simplistically: Axis_Range_Top = Axis_Range_Bottom * qqq_ratio
    pce_axis_max = pce_axis_min * qqq_ratio
    
    # But wait, we want to ensure the actual path 100->125 is visible at the bottom
    # If we set max to 100*5 = 500, then 125 is very low. This is correct for proportional comparison.
    # However, if it's TOO low, it might look like a flat line.
    
    ax3.set_ylim(pce_axis_min, pce_axis_max)
    
    # --------------------------------

    # Format X-Axis Years
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    # Title and Legend
    plt.title('10-Year Financial Trends: QQQ vs Liquidity vs Inflation (PCEPI)', fontsize=16, fontweight='bold')
    
    # Combine legends from all 3 axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    
    ax1.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper left', frameon=True, facecolor='white', framealpha=0.9, fontsize='small')

    # plt.tight_layout() # might conflict with subplots_adjust, use cautiously or manually
    # tight_layout tends to override subplots_adjust. Let's try saving without it first, or use bbox_inches='tight'
    
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    df = load_data()
    plot_trends(df)
