import streamlit as st, pandas as pd
from services.db import init_db, query
from services.inventory import batches,status,money_at_risk,days_left
init_db(); rows=batches()
st.title('📊 Operations Dashboard')
value=sum(x['qty']*x['unit_cost'] for x in rows); expired=sum(1 for x in rows if days_left(x['expiry_date'])<0); soon=sum(1 for x in rows if 0<=days_left(x['expiry_date'])<=7)
a,b,c,d=st.columns(4); a.metric('Inventory Value',f'₹{value:,.0f}'); b.metric('Expiring ≤7 Days',soon); c.metric('Expired Batches',expired); d.metric('Money at Risk (7d)',f'₹{money_at_risk():,.0f}')
st.subheader('Priority Inventory')
df=pd.DataFrame(rows)
if not df.empty:
    df['Status']=df.expiry_date.map(status); df['Days Left']=df.expiry_date.map(days_left); df['Value']=df.qty*df.unit_cost
    st.dataframe(df[['batch_id','ingredient','qty','unit','expiry_date','Days Left','Status','Value']],use_container_width=True,hide_index=True)
st.subheader('Waste Recorded')
w=query("SELECT COALESCE(SUM(t.qty*b.unit_cost),0) v FROM transactions t JOIN batches b ON t.batch_id=b.batch_id WHERE t.type='Waste'")[0]['v']; st.metric('Waste Value',f'₹{w:,.0f}')
