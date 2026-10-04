from .inventory import batches, days_left, waste_value
from .forecasting import forecast, evaluate_models
from .db import query

PERISHABILITY={'Fresh Cream':1.0,'Milk':1.0,'Fish Fillet':1.0,'Coriander':1.0,'Chicken Breast':.9,
'Paneer':.9,'Mutton':.85,'Curd':.8,'Tomato':.75,'Capsicum':.7,'Eggs':.5,'Potato':.35,'Onion':.3}

def ingredient_snapshot(ingredient,horizon=7,multiplier=1.0):
    rows=[b for b in batches() if b['ingredient']==ingredient and days_left(b['expiry_date'])>=0]
    if not rows:return None
    rows.sort(key=lambda b:b['expiry_date'])
    fc=forecast(ingredient,horizon,multiplier)
    demand=sum(x['forecast'] for x in fc)
    daily=demand/horizon if horizon else 0
    stock=sum(b['qty'] for b in rows)
    unit=rows[0]['unit']
    earliest=max(days_left(rows[0]['expiry_date']),0)
    demand_before_expiry=daily*(earliest+1)
    excess=max(rows[0]['qty']-demand_before_expiry,0)
    # Explainable 0-100 score: urgency, excess ratio, perishability.
    urgency=max(0,1-min(earliest,14)/14)
    excess_ratio=min(excess/max(rows[0]['qty'],0.01),1)
    perish=PERISHABILITY.get(ingredient,.45)
    score=round(100*(.45*urgency+.40*excess_ratio+.15*perish))
    level='HIGH' if score>=70 else 'MEDIUM' if score>=45 else 'LOW'
    safety=daily*1.5
    supplier=query("""SELECT s.* FROM suppliers s JOIN batches b ON b.supplier=s.supplier
                      WHERE b.ingredient=? ORDER BY s.lead_time_days,s.on_time_pct DESC LIMIT 1""",(ingredient,))
    supplier=supplier[0] if supplier else None
    lead=supplier['lead_time_days'] if supplier else 2
    lead_demand=daily*lead
    reorder=max(demand+safety-stock,0)
    value_risk=excess*rows[0]['unit_cost']
    ev=evaluate_models(ingredient)
    return {'ingredient':ingredient,'unit':unit,'stock':stock,'forecast_demand':demand,'daily_demand':daily,
            'safety_stock':safety,'coverage_days':stock/daily if daily else 999,'earliest_expiry_days':earliest,
            'predicted_excess':excess,'value_at_risk':value_risk,'risk_score':score,'risk_level':level,
            'recommended_order':reorder,'supplier':supplier,'lead_time_days':lead,'model':ev,'forecast':fc}

def all_snapshots(horizon=7,multiplier=1.0):
    ings=sorted(set(b['ingredient'] for b in batches() if days_left(b['expiry_date'])>=0))
    return [x for x in (ingredient_snapshot(i,horizon,multiplier) for i in ings) if x]

def answer_copilot(question):
    q=question.lower()
    snaps=all_snapshots()
    if not snaps:return "No usable inventory is available."
    risky=sorted(snaps,key=lambda x:(x['risk_score'],x['value_at_risk']),reverse=True)
    reorder=sorted([x for x in snaps if x['recommended_order']>0],key=lambda x:x['recommended_order'],reverse=True)
    if any(k in q for k in ['use first','expire','risk','waste']):
        x=risky[0]
        return (f"Highest priority: {x['ingredient']} has an expiry risk score of {x['risk_score']}/100 "
                f"({x['risk_level']}). The earliest batch expires in {x['earliest_expiry_days']} day(s), "
                f"with about {x['predicted_excess']:.1f} {x['unit']} predicted excess (₹{x['value_at_risk']:,.0f} exposure). "
                f"Action: prioritize FEFO consumption and avoid adding stock until the exposure reduces.")
    if any(k in q for k in ['order','purchase','buy','tomorrow']):
        if not reorder:return "Current stock plus safety stock is sufficient across the forecast horizon; no immediate replenishment is recommended."
        x=reorder[0]; s=x['supplier']
        supplier=f" Preferred supplier: {s['supplier']} ({s['lead_time_days']}-day lead time, {s['on_time_pct']:.0f}% on-time)." if s else ""
        return (f"Top replenishment need: {x['ingredient']}. Forecast demand is {x['forecast_demand']:.1f} {x['unit']} "
                f"for 7 days versus {x['stock']:.1f} {x['unit']} available. Recommended order: "
                f"{x['recommended_order']:.1f} {x['unit']} including ~1.5 days safety stock.{supplier}")
    if 'why' in q:
        x=risky[0]
        return (f"{x['ingredient']} is rated {x['risk_level']} because the score combines days to earliest expiry, "
                f"predicted excess before that expiry, and ingredient perishability. Current score: {x['risk_score']}/100.")
    return ("FreshFlow can answer grounded operational questions such as “What should I use first?”, "
            "“What should I order?”, or “Why is an ingredient high risk?”. Calculations come from the forecasting "
            "and inventory services; this copilot only explains those results.")
