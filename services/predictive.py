from collections import defaultdict
from datetime import date, datetime, timedelta
import math
from .db import query
from .inventory import batches, days_left

# Demo fallback only. These are transparent baseline consumption assumptions used
# until enough observed Consumption transactions exist for an ingredient.
DEMO_DAILY_DEMAND = {
    'Chicken Breast': 6.2, 'Paneer': 3.2, 'Milk': 7.0, 'Fresh Cream': 1.4,
    'Curd': 2.8, 'Fish Fillet': 2.6, 'Mutton': 2.4, 'Eggs': 32.0,
    'Tomato': 6.5, 'Onion': 5.0, 'Capsicum': 2.1, 'Coriander': 1.4,
    'Potato': 5.5, 'Basmati Rice': 7.5, 'Atta': 4.2, 'Toor Dal': 2.5,
    'Cooking Oil': 2.2, 'French Fries': 3.0, 'Frozen Peas': 1.7,
}
SAFETY_DAYS = 1.5

def _observed_daily_demand(ingredient, lookback_days=14):
    rows = query("""SELECT date(created_at) d, SUM(qty) qty
                    FROM transactions
                    WHERE type='Consumption' AND ingredient=?
                      AND datetime(created_at) >= datetime('now', ?)
                    GROUP BY date(created_at) ORDER BY d""",
                 (ingredient, f'-{int(lookback_days)} days'))
    total = sum(r['qty'] for r in rows)
    # Require at least 3 distinct consumption days before treating it as a useful signal.
    if len(rows) >= 3 and total > 0:
        return total / lookback_days, len(rows)
    return None, len(rows)

def demand_rate(ingredient):
    observed, active_days = _observed_daily_demand(ingredient)
    baseline = DEMO_DAILY_DEMAND.get(ingredient)
    if observed is not None:
        return observed, 'Observed 14-day consumption', active_days
    if baseline is not None:
        return baseline, 'Demo baseline (replace with POS/history)', active_days
    # Generic conservative fallback for newly added items.
    current = sum(b['qty'] for b in batches() if b['ingredient'] == ingredient)
    return max(current / 14.0, 0.1), 'Inventory-derived fallback', active_days

def _unit_cost(ingredient):
    rows = [b for b in batches() if b['ingredient'] == ingredient]
    if not rows: return 0
    total_qty = sum(b['qty'] for b in rows)
    if total_qty <= 0: return rows[0]['unit_cost']
    return sum(b['qty'] * b['unit_cost'] for b in rows) / total_qty

def ingredient_prediction(ingredient, horizon=7):
    rows = [b for b in batches() if b['ingredient'] == ingredient and days_left(b['expiry_date']) >= 0]
    if not rows:
        return None
    rows.sort(key=lambda b: (b['expiry_date'], b['received_date']))
    rate, basis, active_days = demand_rate(ingredient)
    total_stock = sum(b['qty'] for b in rows)
    unit = rows[0]['unit']
    cost = _unit_cost(ingredient)

    # Simulate daily demand against FEFO batches through each expiry date.
    remaining_demand_capacity = 0.0
    excess = 0.0
    batch_risks = []
    cumulative_stock = 0.0
    for b in rows:
        d = max(days_left(b['expiry_date']), 0)
        cumulative_stock += b['qty']
        demand_before_expiry = rate * (d + 1)
        excess_cumulative = max(cumulative_stock - demand_before_expiry, 0)
        previous_excess = excess
        excess = max(excess, excess_cumulative)
        batch_excess = max(excess_cumulative - previous_excess, 0)
        if batch_excess > 0:
            batch_risks.append({
                'batch_id': b['batch_id'], 'days_left': d,
                'qty_at_risk': min(batch_excess, b['qty']),
                'value_at_risk': min(batch_excess, b['qty']) * b['unit_cost']
            })

    predicted_excess = min(excess, total_stock)
    value_at_risk = sum(x['value_at_risk'] for x in batch_risks)
    forecast = rate * horizon
    safety_stock = rate * SAFETY_DAYS
    recommended_purchase = max(forecast + safety_stock - total_stock, 0)

    coverage_days = total_stock / rate if rate > 0 else 999
    if predicted_excess > 0 and value_at_risk >= 3000:
        risk = 'HIGH'
    elif predicted_excess > 0:
        risk = 'MEDIUM'
    else:
        risk = 'LOW'

    if predicted_excess > 0:
        recommendation = f'Prioritize FEFO stock and reduce/hold the next order by about {predicted_excess:.1f} {unit}.'
    elif recommended_purchase > 0:
        recommendation = f'Plan to purchase about {recommended_purchase:.1f} {unit} for the next {horizon} days including safety stock.'
    else:
        recommendation = 'Current usable stock covers the forecast window. No immediate purchase is recommended.'

    return {
        'ingredient': ingredient, 'unit': unit, 'stock': total_stock,
        'daily_demand': rate, 'basis': basis, 'observed_days': active_days,
        'forecast_7d': forecast, 'safety_stock': safety_stock,
        'coverage_days': coverage_days, 'predicted_excess': predicted_excess,
        'value_at_risk': value_at_risk, 'recommended_purchase': recommended_purchase,
        'risk': risk, 'recommendation': recommendation, 'batch_risks': batch_risks
    }

def all_predictions(horizon=7):
    ingredients = sorted(set(b['ingredient'] for b in batches() if days_left(b['expiry_date']) >= 0))
    return [p for p in (ingredient_prediction(i, horizon) for i in ingredients) if p]
