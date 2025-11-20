# 2025 APMCM Problem C — Question 1 (Soybean Tariff Shock)

Project for APMCM 2025 Problem C, Q1. It cleans data, calibrates an Armington/CES model for China’s soybean imports from the US/Brazil/Argentina, simulates tariff/price shocks, and visualizes results.

## Project Layout
```
.
├── 2025 APMCM Problems C/      # Official attachments (tariff DB, DataWeb)
├── external_data/
│   ├── wits/                   # WITS By-HS6Product (calendar year, tons, USD)
│   └── psd/                    # USDA PSD world balance (market year, thousand tons)
├── output/
│   ├── external_cleaned/       # Model input and cleaned external data
│   ├── prediction_results/     # Scenario & sensitivity outputs
│   └── images/                 # Plots
├── wash/                       # Official-data cleaning pipeline (general use)
│   └── output/                 # Clean panels from official attachments
├── process_external_data.py    # Clean WITS soybean data → external_cleaned
├── process_psd_soy.py          # Clean PSD table → psd_soy_balance + industry impact table
├── model_q1.py                 # Armington model + scenarios + sensitivities
├── visualization.py            # Plots for historical & simulated results
├── generate_china_data.py      # Optional synthetic data generator
└── README.md
```

- Data sources & units:
  - WITS (external): calendar-year China imports; converted to tons/USD; used as model baseline (`output/external_cleaned/china_soy_imports.csv`).
- PSD (USDA): world balance, market year, values in thousand tons; cleaned to `output/external_cleaned/psd_soy_balance.csv`; used for industry-impact comparison (convert units when comparing to model outputs).
- Official attachments (wash): US-side tariff/exports panels; not directly used by the model.
```text
Assumption sources (external):
- Tariffs: MFN 3% for soybeans; 2018 retaliation +25 p.p.; recent 10% surcharge on US soy (soygrowers, Reuters).
- Freight/logistics: US≈55, AR≈79, BR≈103 USD/ton (Datamar/ERS logistics comparisons; US lowest, BR highest).
- Supply capacity caps: recent export tops ~60Mt (US), ~95Mt (BR), <8Mt raw beans (AR) from USDA/ERS/farmdoc reports.
- Elasticities: demand |η|<1 (e.g., -0.61 short run); substitution 0.7–1.5 range (Armington/EDM studies).
```

## How to Run (Q1 workflow)
1) Clean external soybean data  
```bash
python process_external_data.py
```
Reads `external_data/wits/*.xlsx` (WITS By-HS6Product), keeps US/Brazil/Argentina, computes tons/FOB/tariff, writes `output/external_cleaned/china_soy_imports.csv`.

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

4) (Optional) Clean PSD table and compare industry impact  
```bash
python process_psd_soy.py
```
Outputs:
- `output/external_cleaned/psd_soy_balance.csv`
- `output/prediction_results/industry_impact_psd_export_basis.csv` (scenario 1 delta_q vs PSD exports; PSD in thousand tons, model in tons → convert when interpreting ratios)

5) (Optional) Clean official attachments for broader use  
```bash
python wash/datawash.py
```

## Model Assumptions (model_q1.py)
- Base year: 2024; exporters: US, Brazil, Argentina.
- Substitution elasticity σ = 3.0 (sensitivity 2–8).
- Demand elasticity η = 0.5 (sensitivity 0.15–1.0).
- Transport costs (USD/ton): US 55, Brazil 103, Argentina 79 (aligned to reported logistics order).
- Tariffs in base data: US 13% (3% MFN + 10% surcharge), Brazil/Argentina 3%.
- Scenario 1: +25 p.p. tariff on US only.  
  Scenario 2: Scenario 1 plus US FOB -10%, Brazil/Argentina FOB +5%.
- Supply caps/markups (tons) to avoid “infinite replacement”: US 60M, Brazil 95M, Argentina 8M. No extra demand shock applied (price/elasticity drive demand response).

## Key Outputs
- `output/external_cleaned/china_soy_imports.csv`: Cleaned baseline imports (2015–2024 WITS).
- `output/prediction_results/prediction_results_scenario1.csv` / `scenario2.csv`: q0/q_new, delta_q, pct_change, share_new, V_new.
- `output/prediction_results/sensitivity_analysis_sigma.csv`: US response vs σ.
- `output/prediction_results/sensitivity_analysis_eta.csv`: Total and US response vs η.
- `output/prediction_results/vulnerability_report.txt`: Aggregate volume/price shifts (Scenario 1).
- `output/prediction_results/industry_impact_psd_export_basis.csv`: Scenario 1 delta_q vs PSD exports (unit-aware).
- `output/images/*.png`: All plots.

## Dependencies
- pandas, numpy, openpyxl, matplotlib, seaborn

## Notes
- Model uses external WITS data; wash outputs are available if you build an all-official pipeline.
- When comparing to PSD (thousand tons, market year), convert units and mind year definitions.***
