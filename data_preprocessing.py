import pandas as pd
import numpy as np
import zipfile
import os
from pathlib import Path

# Configuration
DATA_DIR = Path(r"c:\competition\亚太杯\q1\2025 APMCM Problems C\Tariff Data")
OUTPUT_DIR = Path(r"c:\competition\亚太杯\q1\output\cleaned_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Soybean related HTS8 codes (US Tariff Schedule)
SOYBEAN_HTS8 = [
    "12011000",  # Soybeans, seed
    "12019000",  # Soybeans, other than seed
    "12081000",  # Flours and meals of soybeans
    "12089000",  # Other oilseed flours/meals
    "15071000",  # Crude soybean oil
    "15079020",  # Pharm-grade soybean oil
    "15079040",  # Other soybean oil
    "20089961",  # Prepared/preserved soybeans
    "23040000",  # Oilcake/residues from soybeans
]

YEARS = list(range(2020, 2026)) 

def load_us_export_data(export_xlsx_path):
    print(f"Processing Export Data: {export_xlsx_path}")
    try:
        df_raw = pd.read_excel(export_xlsx_path, sheet_name="FAS Value")
    except Exception as e:
        print(f"Error reading {export_xlsx_path}: {e}")
        return pd.DataFrame()
    
    # Row 0 is count, Row 1 is header
    header = df_raw.iloc[1]
    df = df_raw.iloc[2:].copy()
    df.columns = header

    df = df.rename(columns={
        "Data Type": "data_type",
        "HTS Number": "hts2",
        "Description": "description",
        "Country": "country"
    })

    df = df[df["data_type"] == "FAS Value"]

    # Identify year columns (integers or strings looking like years)
    year_cols = [col for col in df.columns if str(col).startswith("20")]
    
    df = df.melt(
        id_vars=["hts2", "description", "country"],
        value_vars=year_cols,
        var_name="year",
        value_name="export_value"
    )
    df["year"] = df["year"].astype(int)
    df["export_value"] = pd.to_numeric(df["export_value"], errors="coerce").fillna(0.0)
    
    return df

def load_us_import_charges(import_xlsx_path):
    print(f"Processing Import Charges Data: {import_xlsx_path}")
    try:
        df_raw = pd.read_excel(import_xlsx_path, sheet_name="General Import Charges")
    except Exception as e:
        print(f"Error reading {import_xlsx_path}: {e}")
        return pd.DataFrame()
    
    header = df_raw.iloc[1]
    df = df_raw.iloc[2:].copy()
    df.columns = header

    df = df.rename(columns={
        "Data Type": "data_type",
        "HTS Number": "hts2",
        "Description": "description",
        "Country": "country"
    })

    df = df[df["data_type"] == "General Import Charges"]

    year_cols = [col for col in df.columns if str(col).startswith("20")]
    
    df = df.melt(
        id_vars=["hts2", "description", "country"],
        value_vars=year_cols,
        var_name="year",
        value_name="import_charges"
    )
    df["year"] = df["year"].astype(int)
    df["import_charges"] = pd.to_numeric(df["import_charges"], errors="coerce").fillna(0.0)

    return df

def compute_mfn_ad_val_equiv(row, unit_price_guess=500.0):
    code = row.get("mfn_rate_type_code")
    ad = row.get("mfn_ad_val_rate")
    if pd.isna(ad): ad = 0.0
    spec = row.get("mfn_specific_rate")
    if pd.isna(spec): spec = 0.0
    other = row.get("mfn_other_rate")
    if pd.isna(other): other = 0.0

    if code == 0: return 0.0
    if code == 7: return ad
    
    base_rate = ad
    # Simplified logic for specific rates
    if code in (1, 3, 4, 6):
        base_rate += spec / unit_price_guess
    if code in (2, 3, 5, 6):
        base_rate += other / unit_price_guess
    
    return base_rate

def load_tariff_for_year(zip_path):
    print(f"Processing Tariff Zip: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            file_list = zf.namelist()
            target_file = None
            # Prefer txt, then xlsx
            for f in file_list:
                if "tariff_database" in f and f.endswith(".txt"):
                    target_file = f
                    break
            
            if not target_file:
                 for f in file_list:
                    if "tariff_database" in f and f.endswith(".xlsx"):
                        target_file = f
                        break
            
            if not target_file:
                print(f"Warning: No tariff database file found in {zip_path}")
                return pd.DataFrame()

            with zf.open(target_file) as f:
                if target_file.endswith(".xlsx"):
                    df = pd.read_excel(f)
                else:
                    # Try pipe first, then comma
                    try:
                        df = pd.read_csv(f, sep="|", encoding='utf-8', low_memory=False)
                        if len(df.columns) < 5: # Suspiciously few columns
                             f.seek(0)
                             df = pd.read_csv(f, sep=",", encoding='utf-8', low_memory=False)
                    except UnicodeDecodeError:
                        f.seek(0)
                        try:
                            df = pd.read_csv(f, sep="|", encoding='latin-1', low_memory=False)
                            if len(df.columns) < 5:
                                f.seek(0)
                                df = pd.read_csv(f, sep=",", encoding='latin-1', low_memory=False)
                        except:
                             f.seek(0)
                             df = pd.read_csv(f, sep=",", encoding='latin-1', low_memory=False)
                    except:
                        f.seek(0)
                        try:
                            df = pd.read_csv(f, sep="|", encoding='latin-1', low_memory=False)
                        except:
                            f.seek(0)
                            df = pd.read_csv(f, sep=",", encoding='latin-1', low_memory=False)

        # Filter for Soybean HTS8
        if "hts8" in df.columns:
            df["hts8"] = df["hts8"].astype(str)
            df = df[df["hts8"].isin(SOYBEAN_HTS8)].copy()
        else:
            print(f"Warning: 'hts8' column not found in {target_file}")
            return pd.DataFrame()

        return df
    except Exception as e:
        print(f"Error processing zip {zip_path}: {e}")
        return pd.DataFrame()

def main():
    # 1. Process Export Data
    export_file = DATA_DIR / "DataWeb-Query-Export.xlsx"
    if export_file.exists():
        df_export = load_us_export_data(export_file)
        if not df_export.empty:
            df_export.to_csv(OUTPUT_DIR / "us_exports_cleaned.csv", index=False)
            print("Saved us_exports_cleaned.csv")
    else:
        print(f"File not found: {export_file}")
    
    # 2. Process Import Charges
    import_file = DATA_DIR / "DataWeb-Query-Import.xlsx"
    if import_file.exists():
        df_import = load_us_import_charges(import_file)
        if not df_import.empty:
            df_import.to_csv(OUTPUT_DIR / "us_import_charges_cleaned.csv", index=False)
            print("Saved us_import_charges_cleaned.csv")
    else:
        print(f"File not found: {import_file}")

    # 3. Process Tariff Data
    tariff_records = []
    for year in YEARS:
        zip_file = DATA_DIR / f"tariff_data_{year}.zip"
        if zip_file.exists():
            df_tariff = load_tariff_for_year(zip_file)
            if not df_tariff.empty:
                df_tariff["mfn_rate_equiv"] = df_tariff.apply(compute_mfn_ad_val_equiv, axis=1)
                df_tariff["year"] = year
                # Select relevant columns
                cols = ["year", "hts8", "brief_description", "mfn_rate_equiv", "mfn_rate_type_code", "mfn_ad_val_rate"]
                # Keep existing columns only
                cols = [c for c in cols if c in df_tariff.columns]
                tariff_records.append(df_tariff[cols])
        else:
            print(f"Zip file not found: {zip_file}")
    
    if tariff_records:
        df_all_tariffs = pd.concat(tariff_records, ignore_index=True)
        df_all_tariffs.to_csv(OUTPUT_DIR / "us_soybean_tariffs_cleaned.csv", index=False)
        print("Saved us_soybean_tariffs_cleaned.csv")
    else:
        print("No tariff data processed.")

if __name__ == "__main__":
    main()
