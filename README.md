# FreshFlow AI — POC V1

Streamlit proof-of-concept for perishable restaurant inventory intelligence.

## Features
- Batch-level receiving and inventory
- Expiry tracking and status
- QR generation per batch
- FEFO / Use First recommendation
- Consumption and waste transactions
- Inventory value and Money-at-Risk dashboard
- SQLite persistence

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Demo story
Receive multiple batches of one ingredient with different expiries, open FEFO to see which batch should be used first, record consumption/waste, then show the dashboard updating.

## Next phase
Demand forecasting, expiry-risk scoring, smart purchase recommendations, invoice OCR, and an AI inventory copilot.


## V3 Predictive Intelligence
Adds explainable consumption-velocity forecasting, batch-level expiry exposure, 7-day demand forecasting, safety-stock-aware purchase recommendations, and transparent forecast-basis labels. Demo baselines are used only when insufficient observed consumption history exists.


## V4 — Decision Intelligence
- 120-day deterministic simulated POS demand history for portfolio demonstration
- Backtested 7-day Moving Average vs Weekday Seasonal Baseline
- MAE/MAPE model evaluation and automatic baseline selection
- Explainable 0–100 expiry-risk score
- Safety-stock-aware Purchase Optimizer with supplier lead-time context
- Grounded Inventory Copilot (tool-style POC; no external LLM API required)
- Scenario Simulator for demand shocks/events

### Important
The seeded demand history is simulated and labelled in the UI. In production, replace `demand_history` with POS/ERP consumption history. The Copilot uses deterministic FreshFlow calculations and does not claim external LLM generation.
