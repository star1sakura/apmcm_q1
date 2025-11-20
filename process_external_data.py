import pandas as pd
from pathlib import Path

# Paths (relative to repo root)
BASE_DIR = Path(__file__).resolve().parent
# WITS data stored under external_data/wits
DATA_DIR = BASE_DIR / "external_data" / "wits"
OUTPUT_DIR = BASE_DIR / "output" / "external_cleaned"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "china_soy_imports.csv"

TARGET_PARTNERS = {
    "United States": "US",
    "Brazil": "Brazil",
    "Argentina": "Argentina"
}

def process_data():
    files = list(DATA_DIR.glob("*.xlsx"))
    all_data = []

    for f in files:
        print(f"Processing {f.name}...")
        try:
            # Read the specific sheet
            df = pd.read_excel(f, sheet_name="By-HS6Product")
            
            # Filter for target partners
            df = df[df["Partner"].isin(TARGET_PARTNERS.keys())].copy()
            
            # Rename partner to standard exporter names
            df["exporter"] = df["Partner"].map(TARGET_PARTNERS)
            
            # Rename and transform columns
            # Trade Value 1000USD -> value_usd (multiply by 1000)
            df["value_usd"] = df["Trade Value 1000USD"] * 1000
            
            # Quantity (Kg) -> quantity_tons (divide by 1000)
            df["quantity_tons"] = df["Quantity"] / 1000
            
            # Calculate FOB Price (USD/Ton)
            df["p_fob"] = df["value_usd"] / df["quantity_tons"]
            
            # Assign Tariff
            # US: 28% (approximate effective rate including retaliatory)
            # Brazil/Argentina: 3% (MFN)
            def get_tariff(exporter):
                if exporter == "US":
                    # Use MFN 3% + recent 10% surcharge (per official notices), pre-scenario
                    return 0.13
                else:
                    return 0.03
            
            df["tariff_china"] = df["exporter"].apply(get_tariff)
            
            # Select final columns
            final_df = df[["Year", "exporter", "quantity_tons", "value_usd", "p_fob", "tariff_china"]].rename(columns={"Year": "year"})
            
            all_data.append(final_df)
            
        except Exception as e:
            print(f"Error processing {f.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values(by=["year", "exporter"])
        
        # Save to CSV
        combined_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nSuccessfully saved processed data to {OUTPUT_FILE}")
        print(combined_df)
    else:
        print("No data processed.")

if __name__ == "__main__":
    process_data()
