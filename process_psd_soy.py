"""
Clean USDA PSD soybeans world balance table and build a simple industry-impact
summary by comparing model scenario results with PSD exports.

Inputs:
    external_data/psd/Table_07_Soybea.csv  (PSD table, as downloaded)
    output/prediction_results/prediction_results_scenario1.csv  (model output)

Outputs:
    output/external_cleaned/psd_soy_balance.csv  (long tidy table: metric, country, year, value)
    output/prediction_results/industry_impact_psd_export_basis.csv
        country, psd_export_2024_25, delta_q (scenario1), delta_q_pct_of_psd_export
"""

import io
from pathlib import Path
from typing import List

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PSD_PATH = BASE_DIR / "external_data" / "psd" / "Table_07_Soybea.csv"
OUTPUT_CLEAN = BASE_DIR / "output" / "external_cleaned" / "psd_soy_balance.csv"
OUTPUT_IMPACT = BASE_DIR / "output" / "prediction_results" / "industry_impact_psd_export_basis.csv"

# Mapping PSD country names to model exporter codes
COUNTRY_MAP = {
    "United States": "US",
    "Brazil": "Brazil",
    "Argentina": "Argentina",
    "China": "China",
}


def parse_psd_table(path: Path) -> pd.DataFrame:
    """Parse the PSD CSV (Table 07) into a tidy long table."""
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    # Skip possible header lines until we see a line starting with comma-separated years
    # In this file, the year header is at line index 2.
    content = "\n".join(raw_lines[2:])
    df = pd.read_csv(io.StringIO(content), skip_blank_lines=True)
    if df.empty:
        raise ValueError("PSD file appears empty after parsing.")

    # First column holds labels
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "label"})

    metrics = {"Production", "Imports", "Exports", "Crush", "Ending Stocks"}
    current_metric: List[str] = []
    m = None
    for lbl in df["label"]:
        if isinstance(lbl, str) and lbl.strip() in metrics:
            m = lbl.strip()
            current_metric.append(m)
        else:
            current_metric.append(m)
    df["metric"] = current_metric

    # Drop rows that are metric headers, unit rows ("nr"), totals (we can keep totals if needed)
    drop_labels = list(metrics) + ["nr", None, float("nan")]
    df = df[~df["label"].isin(drop_labels)].copy()
    df = df.dropna(subset=["metric"])

    # Melt years to long format
    id_vars = ["metric", "label"]
    value_vars = [c for c in df.columns if c not in id_vars]
    long_df = df.melt(id_vars=id_vars, value_vars=value_vars, var_name="year", value_name="value")
    long_df = long_df.dropna(subset=["value"])
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df = long_df.dropna(subset=["value"])
    long_df = long_df.rename(columns={"label": "country"})
    long_df["country"] = long_df["country"].astype(str).str.strip()
    long_df["year"] = long_df["year"].astype(str).str.strip()
    return long_df


def build_impact_vs_psd_exports(psd_long: pd.DataFrame, scenario_csv: Path, psd_year: str = "2024/25") -> pd.DataFrame:
    """Compare model scenario delta_q with PSD exports (specified year).

    Note: PSD exports are in thousand tons; model delta_q is in tons.
    We convert delta_q to thousand tons before computing the ratio.
    """
    exports = (
        psd_long[(psd_long["metric"] == "Exports") & (psd_long["year"] == psd_year)].copy()
    )
    exports["exporter"] = exports["country"].map(COUNTRY_MAP)
    exports = exports.dropna(subset=["exporter"])
    exports = exports[["exporter", "value"]].rename(columns={"value": "psd_export_2024_25"})

    scen = pd.read_csv(scenario_csv)
    scen = scen[["exporter", "delta_q"]].copy()
    scen["delta_q_thousand_tons"] = scen["delta_q"] / 1_000.0

    merged = exports.merge(scen, on="exporter", how="left")
    merged["delta_q_pct_of_psd_export"] = merged["delta_q_thousand_tons"] / merged["psd_export_2024_25"]
    return merged


def main() -> None:
    psd_long = parse_psd_table(PSD_PATH)
    OUTPUT_CLEAN.parent.mkdir(parents=True, exist_ok=True)
    psd_long.to_csv(OUTPUT_CLEAN, index=False)
    print(f"Saved cleaned PSD long table to {OUTPUT_CLEAN}")

    scenario1_path = BASE_DIR / "output" / "prediction_results" / "prediction_results_scenario1.csv"
    if scenario1_path.exists():
        impact = build_impact_vs_psd_exports(psd_long, scenario1_path, psd_year="2024/25")
        impact.to_csv(OUTPUT_IMPACT, index=False)
        print(f"Saved PSD export comparison to {OUTPUT_IMPACT}")
        print(impact)
    else:
        print("Scenario 1 results not found; skipping impact comparison.")


if __name__ == "__main__":
    main()
