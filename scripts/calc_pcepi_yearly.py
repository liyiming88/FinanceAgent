import pandas as pd
import os

# Config
INPUT_FILE = "eval/datas/PCEPI.csv"
OUTPUT_FILE = "eval/datas/PCEPI_yearly_change.csv"

def calculate_yearly_change():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Reading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE, index_col=0, parse_dates=True)
    df.index.name = 'Date'
    df.sort_index(inplace=True)

    # Resample to Yearly, taking the last value of the year (December typically)
    # This represents the index level at the end of the year.
    yearly = df.resample('YE').last()
    
    # Calculate Changes
    # Change from previous year end
    yearly['Previous_Year_End'] = yearly['PCEPI'].shift(1)
    yearly['Change_Absolute'] = yearly['PCEPI'] - yearly['Previous_Year_End']
    yearly['Change_Percent'] = (yearly['Change_Absolute'] / yearly['Previous_Year_End']) * 100
    
    # Clean up for report
    report = yearly[['PCEPI', 'Change_Absolute', 'Change_Percent']].copy()
    report.columns = ['Year_End_Value', 'Yearly_Increase_Points', 'Yearly_Increase_Percent']
    report.index.name = 'Year'
    
    # Format date to just Year
    report.index = report.index.year
    
    # Filter out the first year if it has NaN change (since we don't have previous year data)
    report = report.dropna()

    print("Yearly PCEPI Change:")
    print(report)

    print(f"Saving to {OUTPUT_FILE}...")
    report.to_csv(OUTPUT_FILE)
    print("Done.")

if __name__ == "__main__":
    calculate_yearly_change()
