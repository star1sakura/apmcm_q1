import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output" / "prediction_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = BASE_DIR / "output" / "external_cleaned"  # Processed external soybean data

EXPORTERS = ["US", "Brazil", "Argentina"]
BASE_YEAR = 2024

def load_china_soy_imports(path):
    df = pd.read_csv(path)
    df = df[df["exporter"].isin(EXPORTERS)].copy()
    return df

def calibrate_ces_for_china(china_df, base_year, sigma, eta, transport_cost=None):
    if transport_cost is None:
        transport_cost = {e: 0.0 for e in EXPORTERS}

    base = china_df[china_df["year"] == base_year].copy()
    
    # Calculate CIF Price (FOB + Tariff + Transport)
    # P_cif = (P_fob + Transport) * (1 + Tariff)
    # Note: Tariff is usually applied on CIF value, but here we simplify or assume P_fob includes transport if not specified.
    # Let's follow the formula: P_cif = (P_fob + cost) * (1 + t)
    
    base["cif_price"] = (base["p_fob"] + base["exporter"].map(transport_cost)) * (1 + base["tariff_china"])

    Q0 = base["quantity_tons"].sum()
    V0 = base["value_usd"].sum()

    # Share by value (expenditure share)
    # In CES, s_i = (alpha_i * p_i^{1-sigma}) / P^{1-sigma}
    # Let's use the standard calibration:
    # alpha_i_tilde = s_i * p_i^{sigma-1}
    
    # Calculate expenditure shares
    # Total Expenditure E = Sum(p_cif * q)
    # Note: value_usd in data is likely FOB value. 
    # We should calculate CIF Value for the model weights.
    base["value_cif"] = base["quantity_tons"] * base["cif_price"]
    Total_CIF_Value = base["value_cif"].sum()
    
    base["share_val"] = base["value_cif"] / Total_CIF_Value

    # Calibrate Alpha
    # alpha_i = share_i * (p_i)^(sigma-1)
    base["alpha_tilde"] = base["share_val"] * (base["cif_price"] ** (sigma - 1))
    
    # Normalize alphas so they sum to 1 (optional but good for interpretation)
    alpha_sum = base["alpha_tilde"].sum()
    base["alpha"] = base["alpha_tilde"] / alpha_sum

    # Price Index P0
    # P = (Sum alpha_i * p_i^(1-sigma))^(1/(1-sigma))
    tmp = (base["alpha"] * (base["cif_price"] ** (1 - sigma))).sum()
    P0 = tmp ** (1 / (1 - sigma))

    # Calibrate Demand Shifter A_C
    # Q = A_C * P^(-eta)  => A_C = Q / P^(-eta)
    A_C = Q0 / (P0 ** (-eta))

    params = {
        "base_year": base_year,
        "sigma": sigma,
        "eta": eta,
        "A_C": A_C,
        "P0": P0,
        "Q0": Q0,
        "alpha_i": base.set_index("exporter")["alpha"].to_dict(),
        "p0_i": base.set_index("exporter")["p_fob"].to_dict(),
        "q0_i": base.set_index("exporter")["quantity_tons"].to_dict(),
        "tariff0_i": base.set_index("exporter")["tariff_china"].to_dict(),
        "transport_cost": transport_cost,
    }
    return params

def simulate_scenario_for_china(params, scenario):
    sigma = params["sigma"]
    eta = params["eta"]
    A_C = params["A_C"]
    alpha_i = params["alpha_i"]
    p0_i = params["p0_i"]
    transport_cost = params["transport_cost"]
    tariff0_i = params["tariff0_i"]

    records = []
    for exp in EXPORTERS:
        base_tariff = tariff0_i[exp]
        scen_info = scenario.get(exp, {})
        
        # Determine new tariff
        if "new_tariff" in scen_info:
            t_new = scen_info["new_tariff"]
        else:
            delta = scen_info.get("delta_tariff", 0.0)
            t_new = base_tariff + delta
            
        # Determine new FOB price (if world price changes)
        # Default to P0 if not specified
        p_fob_new = scen_info.get("new_p_fob", p0_i[exp])
        
        # Calculate new CIF
        tau = transport_cost.get(exp, 0.0)
        c_new = (p_fob_new + tau) * (1 + t_new)

        records.append({
            "exporter": exp,
            "tariff_new": t_new,
            "p_fob_new": p_fob_new,
            "cif_price_new": c_new,
            "alpha": alpha_i[exp]
        })

    df = pd.DataFrame(records)

    # New Price Index
    tmp = (df["alpha"] * (df["cif_price_new"] ** (1 - sigma))).sum()
    P_new = tmp ** (1 / (1 - sigma))

    # New Total Demand
    Q_new = A_C * (P_new ** (-eta))

    # New Shares
    # s_i = alpha_i * (p_i / P)^(1-sigma)
    #     = alpha_i * p_i^(1-sigma) * P^(sigma-1)
    numerator = df["alpha"] * (df["cif_price_new"] ** (1 - sigma))
    
    # DEBUG
    # print("\n--- DEBUG ---")
    # print(df[["exporter", "tariff_new", "p_fob_new", "cif_price_new"]])
    # print("Numerator:", numerator)
    # END DEBUG

    denominator = numerator.sum()
    df["share_new"] = numerator / denominator

    # DEBUG PRINT
    # print("\n--- DEBUG SIMULATION ---")
    # print(df[["exporter", "tariff_new", "p_fob_new", "cif_price_new", "share_new"]])
    # ------------------------

    # New Quantities
    # share_new is Value Share (s_i = p_i q_i / P Q)
    # So q_i = (s_i * P * Q) / p_i
    total_expenditure = P_new * Q_new
    df["q_new"] = (df["share_new"] * total_expenditure) / df["cif_price_new"]
    
    # New Export Values (FOB basis)
    df["V_new"] = df["q_new"] * df["p_fob_new"]

    # Comparison
    q0_i = params["q0_i"]
    df["q0"] = df["exporter"].map(q0_i)
    df["delta_q"] = df["q_new"] - df["q0"]
    df["pct_change_q"] = df["delta_q"] / df["q0"]
    
    return df

def main():
    # 1. Load Data
    china_imports_path = DATA_DIR / "china_soy_imports.csv"
    if not china_imports_path.exists():
        print("Error: china_soy_imports.csv not found.")
        return
        
    china_imports = load_china_soy_imports(china_imports_path)
    
    # 2. Calibrate
    # Assumptions
    sigma = 4.0 # Substitution elasticity
    eta = 0.3   # Demand elasticity
    transport_costs = {"US": 20.0, "Brazil": 25.0, "Argentina": 23.0}
    
    print(f"Calibrating model to Base Year: {BASE_YEAR}")
    params = calibrate_ces_for_china(
        china_imports, 
        BASE_YEAR, 
        sigma, 
        eta, 
        transport_costs
    )
    
    # 3. Define Scenarios
    # Scenario 1: China Retaliates against US (+25% tariff on US Soy)
    # US "Reciprocal Tariff" policy triggers this.
    # Assume Brazil/Argentina tariffs stay same.
    
    scenario_1 = {
        "US": {"delta_tariff": 0.25},
        "Brazil": {"delta_tariff": 0.0},
        "Argentina": {"delta_tariff": 0.0}
    }
    
    print("\nRunning Scenario 1: China imposes +25% tariff on US Soybeans")
    res1 = simulate_scenario_for_china(params, scenario_1)
    
    # Formatting output
    cols = ["exporter", "q0", "q_new", "delta_q", "pct_change_q", "V_new", "share_new"]
    print(res1[cols].to_string(float_format="%.2f"))
    
    # Save results
    res1.to_csv(OUTPUT_DIR / "prediction_results_scenario1.csv", index=False)
    print(f"\nResults saved to {OUTPUT_DIR / 'prediction_results_scenario1.csv'}")

    # --- Supply Chain Vulnerability Analysis ---
    print("\n--- Supply Chain Vulnerability Analysis (Scenario 1) ---")
    
    # 1. Import Volume Loss
    total_q0 = res1["q0"].sum()
    total_q_new = res1["q_new"].sum()
    vul_q = (total_q0 - total_q_new) / total_q0
    
    # 2. Price Increase (Weighted Average CIF Price)
    # Reconstruct Base CIF Prices: cif_0 = (p_fob + transport) * (1 + tariff)
    cif_0_list = []
    for exp in res1["exporter"]:
        p_fob = params["p0_i"][exp]
        tau = params["transport_cost"].get(exp, 0.0)
        t0 = params["tariff0_i"][exp]
        cif = (p_fob + tau) * (1 + t0)
        cif_0_list.append(cif)
    
    res1["cif_price_0"] = cif_0_list
    
    # Weighted Averages
    avg_p0 = (res1["cif_price_0"] * res1["q0"]).sum() / total_q0
    avg_p_new = (res1["cif_price_new"] * res1["q_new"]).sum() / total_q_new
    
    vul_p = (avg_p_new - avg_p0) / avg_p0
    
    print(f"Baseline Total Import: {total_q0/1e6:.2f} Million Tons")
    print(f"Scenario Total Import: {total_q_new/1e6:.2f} Million Tons")
    print(f"Import Volume Loss (Vul_Q): {vul_q:.2%}")
    
    print(f"Baseline Avg CIF Price: ${avg_p0:.2f}/Ton")
    print(f"Scenario Avg CIF Price: ${avg_p_new:.2f}/Ton")
    print(f"Price Increase (Vul_P): {vul_p:.2%}")
    
    # Save to text file
    with open(OUTPUT_DIR / "vulnerability_report.txt", "w", encoding="utf-8") as f:
        f.write("Supply Chain Vulnerability Analysis (Scenario 1)\n")
        f.write("================================================\n")
        f.write(f"Import Volume Loss (Vul_Q): {vul_q:.4f} ({vul_q:.2%})\n")
        f.write(f"Price Increase (Vul_P):     {vul_p:.4f} ({vul_p:.2%})\n\n")
        f.write("Details:\n")
        f.write(f"Baseline Total Import: {total_q0:,.2f} Tons\n")
        f.write(f"Scenario Total Import: {total_q_new:,.2f} Tons\n")
        f.write(f"Baseline Avg Price:    ${avg_p0:.2f}\n")
        f.write(f"Scenario Avg Price:    ${avg_p_new:.2f}\n")
    print(f"Vulnerability report saved to {OUTPUT_DIR / 'vulnerability_report.txt'}")

    # Scenario 2: US Price drops due to glut, Brazil Price rises due to demand
    # US Price -10%, Brazil/Arg Price +5%
    # Plus the tariff
    scenario_2 = {
        "US": {
            "delta_tariff": 0.25,
            "new_p_fob": params["p0_i"]["US"] * 0.90
        },
        "Brazil": {
            "delta_tariff": 0.0,
            "new_p_fob": params["p0_i"]["Brazil"] * 1.05
        },
        "Argentina": {
            "delta_tariff": 0.0,
            "new_p_fob": params["p0_i"]["Argentina"] * 1.05
        }
    }
    
    print("\nRunning Scenario 2: Tariff + Price Effects (US -10%, Others +5%)")
    res2 = simulate_scenario_for_china(params, scenario_2)
    print(res2[cols].to_string(float_format="%.2f"))
    res2.to_csv(OUTPUT_DIR / "prediction_results_scenario2.csv", index=False)

    # 4. Sensitivity Analysis (Sigma)
    print("\nRunning Sensitivity Analysis on Sigma (Substitution Elasticity)...")
    sigmas = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0]
    sensitivity_records = []
    
    # Use Scenario 1 for sensitivity test
    base_scenario = scenario_1
    
    for s in sigmas:
        # Recalibrate with new sigma
        p = calibrate_ces_for_china(china_imports, BASE_YEAR, s, eta, transport_costs)
        # Run simulation
        res = simulate_scenario_for_china(p, base_scenario)
        
        # Extract US change
        us_res = res[res["exporter"] == "US"].iloc[0]
        sensitivity_records.append({
            "sigma": s,
            "us_pct_change": us_res["pct_change_q"],
            "us_share_new": us_res["share_new"],
            "brazil_share_new": res[res["exporter"] == "Brazil"].iloc[0]["share_new"]
        })
    
    df_sens = pd.DataFrame(sensitivity_records)
    df_sens.to_csv(OUTPUT_DIR / "sensitivity_analysis_sigma.csv", index=False)
    print(f"Sensitivity analysis saved to {OUTPUT_DIR / 'sensitivity_analysis_sigma.csv'}")
    print(df_sens.to_string(float_format="%.4f"))

if __name__ == "__main__":
    main()
