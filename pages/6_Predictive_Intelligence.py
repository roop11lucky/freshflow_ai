import streamlit as st
import pandas as pd
import plotly.express as px
from services.db import init_db
from services.predictive import all_predictions, ingredient_prediction

init_db()
st.title('🧠 Predictive Intelligence')
st.caption('Explainable demand, expiry-risk and purchase recommendations derived from current stock + consumption velocity.')

preds = all_predictions(7)
if not preds:
    st.info('No usable inventory is available for prediction.')
    st.stop()

df = pd.DataFrame([{k:v for k,v in p.items() if k != 'batch_risks'} for p in preds])
total_risk = df['value_at_risk'].sum()
high = int((df['risk']=='HIGH').sum())
purchase = df['recommended_purchase'].sum()

c1,c2,c3,c4 = st.columns(4)
c1.metric('Predicted Expiry Exposure', f'₹{total_risk:,.0f}')
c2.metric('High-Risk Ingredients', high)
c3.metric('7-Day Forecast Items', len(df))
c4.metric('Items to Reorder', int((df['recommended_purchase']>0).sum()))

st.info('ℹ️ POC methodology: when enough real consumption history exists, FreshFlow uses observed 14-day velocity. Until then, seeded demo demand baselines are clearly labelled. These are explainable forecasts, not claimed trained-ML probabilities.')

left,right = st.columns(2)
with left:
    st.subheader('⚠️ Predicted Expiry Exposure')
    riskdf = df[df.value_at_risk > 0].sort_values('value_at_risk',ascending=False)
    if riskdf.empty: st.success('No predicted excess before expiry.')
    else:
        st.plotly_chart(px.bar(riskdf,x='ingredient',y='value_at_risk',
                               labels={'ingredient':'Ingredient','value_at_risk':'Predicted value at risk (₹)'}),
                        use_container_width=True)
with right:
    st.subheader('📈 Stock vs 7-Day Demand')
    comp = df[['ingredient','stock','forecast_7d']].melt('ingredient',var_name='Metric',value_name='Quantity')
    st.plotly_chart(px.bar(comp,x='ingredient',y='Quantity',color='Metric',barmode='group'),
                    use_container_width=True)

st.subheader('🎯 Ingredient Intelligence')
ingredient = st.selectbox('Select ingredient', df['ingredient'].tolist())
p = ingredient_prediction(ingredient,7)

a,b,c,d = st.columns(4)
a.metric('Current Stock', f"{p['stock']:.1f} {p['unit']}")
b.metric('Daily Demand', f"{p['daily_demand']:.1f} {p['unit']}")
c.metric('7-Day Forecast', f"{p['forecast_7d']:.1f} {p['unit']}")
d.metric('Stock Coverage', f"{p['coverage_days']:.1f} days")

a,b,c = st.columns(3)
a.metric('Expiry Risk', p['risk'])
b.metric('Predicted Excess', f"{p['predicted_excess']:.1f} {p['unit']}")
c.metric('Recommended Purchase', f"{p['recommended_purchase']:.1f} {p['unit']}")

if p['risk']=='HIGH':
    st.error(f"🚨 FreshFlow Recommendation: {p['recommendation']}")
elif p['risk']=='MEDIUM':
    st.warning(f"⚠️ FreshFlow Recommendation: {p['recommendation']}")
else:
    st.success(f"✅ FreshFlow Recommendation: {p['recommendation']}")

st.caption(f"Forecast basis: **{p['basis']}** · Safety stock: {p['safety_stock']:.1f} {p['unit']} (~1.5 days demand)")

if p['batch_risks']:
    st.subheader('Batch-level predicted risk')
    br = pd.DataFrame(p['batch_risks'])
    br['value_at_risk'] = br['value_at_risk'].map(lambda x:f'₹{x:,.0f}')
    st.dataframe(br.rename(columns={'batch_id':'Batch','days_left':'Days Left','qty_at_risk':'Qty at Risk','value_at_risk':'Value at Risk'}),
                 use_container_width=True,hide_index=True)

st.subheader('🛒 7-Day Purchase Recommendations')
orders = df[['ingredient','stock','forecast_7d','safety_stock','predicted_excess','recommended_purchase','risk','basis']].copy()
orders.columns = ['Ingredient','Current Stock','7-Day Demand','Safety Stock','Predicted Excess','Recommended Purchase','Expiry Risk','Forecast Basis']
st.dataframe(orders.sort_values(['Expiry Risk','Recommended Purchase'],ascending=[True,False]),
             use_container_width=True,hide_index=True)
