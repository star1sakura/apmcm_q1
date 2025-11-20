import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(r"c:\competition\亚太杯\q1\output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_data():
    # Generate data for 2020-2024 (Historical/Current)
    # 2025 is the "Shock" year, but we might want baseline data up to 2024.
    years = range(2020, 2025) 
    exporters = ["US", "Brazil", "Argentina"]
    
    records = []
    
    # Base assumptions (approximate for simulation)
    # Total China Import ~ 100M tons
    # Shares: Brazil ~60%, US ~30%, Argentina ~5-10%
    
    np.random.seed(42) # For reproducibility

    for year in years:
        # Total import volume trend (slightly increasing)
        total_import = 100_000_000 * (1 + (year - 2020) * 0.02) * np.random.uniform(0.95, 1.05)
        
        # Base price trend (fluctuating)
        # 2020: ~400, 2021: ~500, 2022: ~600, 2023: ~550, 2024: ~500
        if year == 2020: base_price = 400
        elif year == 2021: base_price = 520
        elif year == 2022: base_price = 600
        elif year == 2023: base_price = 550
        else: base_price = 500
        
        base_price = base_price * np.random.uniform(0.95, 1.05)

        # Shares
        # Brazil
        share_br = 0.60 + np.random.uniform(-0.05, 0.05)
        # US (fluctuates more due to relations)
        share_us = 0.30 + np.random.uniform(-0.05, 0.05)
        # Argentina
        share_ar = 1.0 - share_br - share_us
        if share_ar < 0: share_ar = 0.01
        
        shares = {"Brazil": share_br, "US": share_us, "Argentina": share_ar}
        
        for exp in exporters:
            share = shares[exp]
            quantity = total_import * share
            
            # Price differentiation
            # US usually slightly higher quality/price? Or Brazil cheaper?
            # Let's assume small random variation around base price
            price = base_price * np.random.uniform(0.98, 1.02)
            
            value = quantity * price
            
            # Tariff
            # MFN is 3%
            # US faced 25% additional in some years, but waivers were common.
            # For the model baseline, we often use the "applied" rate.
            # Let's use 3% for all to represent a "Normal Trade" baseline for the model calibration,
            # or we can use 28% for US if we want to capture the trade war status.
            # Given the problem asks about NEW 2025 tariffs, let's assume the 2024 baseline 
            # has normalized somewhat or we use effective rates.
            # Let's stick to 0.03 (3%) for simplicity in this simulated dataset, 
            # assuming waivers were in place for the volume that DID enter.
            tariff = 0.03
            
            records.append({
                "year": year,
                "exporter": exp,
                "quantity_tons": int(quantity),
                "value_usd": value,
                "p_fob": price,
                "tariff_china": tariff
            })
            
    df = pd.DataFrame(records)
    output_path = OUTPUT_DIR / "china_soy_imports.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    generate_data()
