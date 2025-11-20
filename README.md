# 2025 APMCM Problem C — Question 1 (Soybean Tariff Shock)

Project for APMCM 2025 Problem C, Question 1. It cleans data, calibrates an Armington/CES model for China’s soybean imports from the US/Brazil/Argentina, simulates tariff/price shocks, and visualizes results.

## Project Layout
```
.
├── 2025 APMCM Problems C/      # Official attachments (tariff DB, DataWeb)
├── external_data/              # Extra data for Q1 (WITS China soybean imports)
├── output/
│   ├── external_cleaned/       # Cleaned external soybean data (model input)
│   ├── prediction_results/     # Scenario & sensitivity outputs
│   └── images/                 # Plots
├── wash/                       # Official-data cleaning pipeline (general use)
│   └── output/                 # Clean panels from official attachments
├── process_external_data.py    # Clean WITS soybean data → external_cleaned
├── model_q1.py                 # Armington model + scenarios + sensitivities
├── visualization.py            # Plots for historical & simulated results
├── generate_china_data.py      # Optional synthetic data generator
└── README.md
```

## How to Run (Q1 workflow)
1) Clean external soybean data  
```bash
python process_external_data.py
```
Reads `external_data/*.xlsx` (WITS By-HS6Product), keeps US/Brazil/Argentina, computes tons/FOB/tariff, writes `output/external_cleaned/china_soy_imports.csv`.

2) Run model (calibration + scenarios + sensitivity)  
```bash
python model_q1.py
```
Outputs to `output/prediction_results/`:
- `prediction_results_scenario1.csv` (China +25 p.p. tariff on US)
- `prediction_results_scenario2.csv` (tariff + US FOB -10%, others +5%)
- `sensitivity_analysis_sigma.csv` (σ sweep)
- `sensitivity_analysis_eta.csv` (η sweep)
- `vulnerability_report.txt`

3) Generate plots  
```bash
python visualization.py
```
Writes to `output/images/`:
- Historical trends (`1_historical_quantity_trend.png`, `2_historical_share_trend.png`)
- Scenario volume bars (`3a_volume_impact.png`, `3b_volume_impact.png`)
- Share pies (`4_share_comparison_pie.png`)
- Sensitivities (`5_sensitivity_sigma.png`, `6_sensitivity_eta.png`)

4) (Optional) Clean official attachments for broader use  
```bash
python wash/datawash.py
```
Produces general tariff/trade panels in `wash/output/` (not directly used by Q1 model but useful for other questions).

## Model Assumptions (model_q1.py)
- Base year: 2024; exporters: US, Brazil, Argentina.
- Substitution elasticity σ = 4.0 (sensitivity 2–8).
- Demand elasticity η = 0.8 (sensitivity 0.1–1.2).
- Transport costs (USD/ton): US 20, Brazil 25, Argentina 23.
- Tariffs in base data: US 28%, Brazil/Argentina 3%.
- Scenario 1: +25 p.p. tariff on US only.  
  Scenario 2: Scenario 1 plus US FOB -10%, Brazil/Argentina FOB +5%.

## Key Outputs
- `output/external_cleaned/china_soy_imports.csv`: Cleaned baseline imports (2020–2024).
- `output/prediction_results/prediction_results_scenario1.csv`/`scenario2.csv`: q0/q_new, delta_q, pct_change, share_new, V_new.
- `output/prediction_results/sensitivity_analysis_sigma.csv`: US response vs σ.
- `output/prediction_results/sensitivity_analysis_eta.csv`: Total and US response vs η.
- `output/prediction_results/vulnerability_report.txt`: Aggregate volume/price shifts (Scenario 1).
- `output/images/*.png`: All plots for reporting.

## Dependencies
- pandas, numpy, openpyxl, matplotlib, seaborn

## Notes
- The Q1 model currently uses external WITS data for China’s soybean imports; official attachment panels are available via `wash/` if you need an all-official-data pipeline.
- If overall import rises under tariffs and you prefer a demand contraction, raise η or increase the price/tariff shock in the scenarios.***
