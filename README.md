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
