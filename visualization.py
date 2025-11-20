import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.font_manager as fm

# Configuration
DATA_DIR = Path(r"c:\competition\亚太杯\q1\output\cleaned_data")
PRED_DIR = Path(r"c:\competition\亚太杯\q1\output\prediction_results")
IMG_DIR = Path(r"c:\competition\亚太杯\q1\output\images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

# Set style and font
sns.set_theme(style="whitegrid")
# Try to find a font that supports Chinese, fallback to standard sans-serif
# In a standard Windows env, SimHei or Microsoft YaHei usually works.
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

def plot_historical_trends():
    print("Generating historical trend charts...")
    df = pd.read_csv(DATA_DIR / "china_soy_imports.csv")
    
    # 1. Quantity Trend (Line Chart)
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x="year", y="quantity_tons", hue="exporter", marker="o", linewidth=2.5)
    plt.title("2020-2024 China Soybean Import Quantity by Source")
    plt.ylabel("Quantity (Tons)")
    plt.xlabel("Year")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(IMG_DIR / "1_historical_quantity_trend.png", dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Market Share Trend (Stacked Bar Chart)
    df_pivot = df.pivot(index="year", columns="exporter", values="quantity_tons")
    df_share = df_pivot.div(df_pivot.sum(axis=1), axis=0)
    
    df_share.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='viridis', alpha=0.85)
    plt.title("2020-2024 China Soybean Import Market Share Structure")
    plt.ylabel("Market Share")
    plt.xlabel("Year")
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "2_historical_share_trend.png", dpi=300)
    plt.close()

def plot_scenario_impact(scenario_file, scenario_name, file_prefix):
    print(f"Generating charts for {scenario_name}...")
    df = pd.read_csv(PRED_DIR / scenario_file)
    
    # Prepare data for plotting (Melt q0 and q_new)
    plot_data = df.melt(id_vars=["exporter"], value_vars=["q0", "q_new"], var_name="Type", value_name="Quantity")
    plot_data["Type"] = plot_data["Type"].map({"q0": "Baseline (2024)", "q_new": "Predicted"})
    
    # 3. Bar Chart Comparison (Before vs After)
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=plot_data, x="exporter", y="Quantity", hue="Type", palette="muted")
    
    # Add value labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f', padding=3, fontsize=9)
        
    plt.title(f"Impact on Export Volume: {scenario_name}")
    plt.ylabel("Quantity (Tons)")
    plt.xlabel("Exporter")
    plt.savefig(IMG_DIR / f"{file_prefix}_volume_impact.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_share_comparison_pie():
    print("Generating market share comparison pie charts...")
    # Load data
    df1 = pd.read_csv(PRED_DIR / "prediction_results_scenario1.csv")
    
    # Baseline Shares (calculated from q0)
    total_q0 = df1["q0"].sum()
    shares_0 = df1["q0"] / total_q0
    labels = df1["exporter"]
    
    # Scenario 1 Shares
    shares_1 = df1["share_new"]
    
    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    
    # Colors
    colors = sns.color_palette("pastel")
    
    # Text properties for pie chart labels
    textprops = {'fontsize': 12}

    # Pie 1: Baseline
    axes[0].pie(shares_0, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, 
                wedgeprops={'edgecolor': 'white'}, textprops=textprops)
    axes[0].set_title("Baseline Market Share (2024)", fontsize=16, pad=10)
    
    # Pie 2: Scenario 1
    axes[1].pie(shares_1, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors,
                wedgeprops={'edgecolor': 'white'}, textprops=textprops)
    axes[1].set_title("Scenario 1: Post-Tariff Market Share", fontsize=16, pad=10)
    
    plt.suptitle("Impact of Tariff Shock on Market Structure", fontsize=20)
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(IMG_DIR / "4_share_comparison_pie.png", dpi=300)
    plt.close()

def plot_sensitivity_analysis():
    print("Generating sensitivity analysis chart...")
    sens_file = PRED_DIR / "sensitivity_analysis_sigma.csv"
    if not sens_file.exists():
        print("Sensitivity data not found, skipping...")
        return

    df = pd.read_csv(sens_file)
    
    plt.figure(figsize=(10, 6))
    
    # Plot US % Change vs Sigma
    # Create a twin axis to show Share on right
    ax1 = plt.gca()
    
    # Line 1: US Export Change % (Left Axis)
    line1 = ax1.plot(df["sigma"], df["us_pct_change"] * 100, marker='o', linewidth=2.5, 
             color='#d62728', label="US Export Change (%)")
    ax1.set_xlabel("Substitution Elasticity ($\sigma$)", fontsize=12)
    ax1.set_ylabel("US Export Volume Change (%)", color='#d62728', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#d62728')
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Set y-limits to make them visually distinct if needed, or let them auto-scale
    # Auto-scale is usually fine, but if they overlap perfectly, it means the relationship is linear.
    # Let's force the right axis to start from 0 to see the share better.
    
    # Line 2: US Market Share (Right Axis)
    ax2 = ax1.twinx()
    line2 = ax2.plot(df["sigma"], df["us_share_new"] * 100, marker='s', linewidth=2.5, 
             color='#1f77b4', linestyle='--', label="US New Market Share (%)")
    ax2.set_ylabel("US New Market Share (%)", color='#1f77b4', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#1f77b4')
    ax2.set_ylim(0, 30) # Force scale to show share clearly (0-30%)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right')
    
    plt.title("Sensitivity Analysis: Impact of Elasticity ($\sigma$) on US Exports", fontsize=14)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "5_sensitivity_sigma.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    plot_historical_trends()
    plot_scenario_impact("prediction_results_scenario1.csv", "Scenario 1 (Tariff Only)", "3a")
    plot_scenario_impact("prediction_results_scenario2.csv", "Scenario 2 (Tariff + Price Adj)", "3b")
    plot_share_comparison_pie()
    plot_sensitivity_analysis()
    print(f"\nAll images saved to {IMG_DIR}")
