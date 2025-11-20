import pandas as pd
from pathlib import Path

data_dir = Path(r"c:\competition\亚太杯\q1\external_data")
files = list(data_dir.glob("*.xlsx"))

for f in files:
    print(f"--- Inspecting {f.name} ---")
    try:
        xl = pd.ExcelFile(f)
        print("Sheet names:", xl.sheet_names)
        for sheet in xl.sheet_names:
            if sheet == 'By-HS6Product':
                print(f"  Sheet: {sheet}")
                df = pd.read_excel(f, sheet_name=sheet, header=0)
                print("Columns:", df.columns.tolist())
                print(df[['Year', 'Partner', 'Trade Value 1000USD', 'Quantity']].head())
    except Exception as e:
        print(f"Error reading {f.name}: {e}")
    print("\n")
