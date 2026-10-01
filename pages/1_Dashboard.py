import streamlit as st
import pandas as pd
import plotly.express as px
from services.db import init_db
from services.inventory import batches, status, days_left, dashboard_summary, transaction_history

init_db()
st.title('📊 FreshFlow Operations Center')
st.caption('Live operational view derived from batch inventory and kitchen transactions.')

rows = batches()
s = dashboard_summary()

c1,c2,c3,c4 = st.columns(4)
c1.metric('Inventory Value', f"₹{s['inventory_value']:,.0f}")
c2.metric('Money at Risk · 7d', f"₹{s['money_at_risk_7d']:,.0f}")
c3.metric('Expiring ≤3 Days', s['expiring_3d'])
c4.metric('Waste · 30d', f"₹{s['waste_30d']:,.0f}", f"{s['waste_pct_30d']:.1f}% of used + wasted")

c5,c6,c7,c8 = st.columns(4)
c5.metric('Active Batches', s['active_batches'])
c6.metric('FEFO Actions', s['fefo_actions'])
c7.metric('Expired Batches', s['expired_batches'])
c8.metric('Expired Stock Value', f"₹{s['expired_value']:,.0f}")

if not rows:
    st.info('No inventory available.')
    st.stop()

df = pd.DataFrame(rows)
df['Days Left'] = df['expiry_date'].map(days_left)
df['Status'] = df['expiry_date'].map(status)
df['Value'] = df['qty'] * df['unit_cost']

st.subheader('🚨 Immediate Actions')
priority = df[df['Days Left'] <= 3].sort_values(['Days Left','Value'], ascending=[True,False]).head(8)
if priority.empty:
    st.success('No batches require immediate expiry action.')
else:
    for _, r in priority.iterrows():
        if r['Days Left'] < 0:
            st.error(f"EXPIRED · {r['ingredient']} · {r['batch_id']} · {r['qty']:g} {r['unit']} · ₹{r['Value']:,.0f} stock value")
        elif r['Days Left'] <= 1:
            st.error(f"USE FIRST · {r['ingredient']} · {r['batch_id']} · expires in {r['Days Left']} day(s) · ₹{r['Value']:,.0f} at risk")
        else:
            st.warning(f"PRIORITIZE · {r['ingredient']} · {r['batch_id']} · expires in {r['Days Left']} days · ₹{r['Value']:,.0f} at risk")

left,right = st.columns(2)
with left:
    st.subheader('💰 Money at Risk by Ingredient')
    risk = df[(df['Days Left'] >= 0) & (df['Days Left'] <= 7)].groupby('ingredient',as_index=False)['Value'].sum().sort_values('Value',ascending=False)
    if not risk.empty:
        st.plotly_chart(px.bar(risk,x='ingredient',y='Value',labels={'ingredient':'Ingredient','Value':'Value at Risk (₹)'}),use_container_width=True)
    else: st.info('No inventory at risk in the next 7 days.')
with right:
    st.subheader('⏳ Expiry Risk Distribution')
    def bucket(d):
        if d < 0: return 'Expired'
        if d <= 1: return '<24–48h'
        if d <= 3: return '2–3 days'
        if d <= 7: return '4–7 days'
        return 'Safe >7d'
    df['Risk Window'] = df['Days Left'].map(bucket)
    dist = df.groupby('Risk Window',as_index=False)['Value'].sum()
    st.plotly_chart(px.pie(dist,names='Risk Window',values='Value',hole=.55),use_container_width=True)

st.subheader('📦 Priority Batch Inventory')
show = df.sort_values(['Days Left','Value'],ascending=[True,False]).copy()
show['Value'] = show['Value'].map(lambda x:f'₹{x:,.0f}')
st.dataframe(show[['batch_id','ingredient','supplier','qty','unit','expiry_date','Days Left','Status','Value']],use_container_width=True,hide_index=True)

st.subheader('🕘 Recent Operations Feed')
tx = pd.DataFrame(transaction_history(12))
if tx.empty:
    st.caption('Transactions will appear here as the kitchen consumes or wastes stock.')
else:
    tx['Value'] = tx['value'].fillna(0).map(lambda x:f'₹{x:,.0f}')
    st.dataframe(tx[['created_at','type','ingredient','batch_id','qty','unit','reason','Value']],use_container_width=True,hide_index=True)
