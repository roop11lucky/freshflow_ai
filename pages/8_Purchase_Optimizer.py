import streamlit as st,pandas as pd
from services.db import init_db
from services.intelligence import all_snapshots
init_db(); st.title('🛒 Purchase Optimizer')
st.caption('Forecast demand + safety stock − usable inventory, enriched with supplier lead-time context.')
rows=all_snapshots()
data=[]
for x in rows:
    s=x['supplier'] or {}
    data.append({'Ingredient':x['ingredient'],'Stock':round(x['stock'],1),'7-Day Demand':round(x['forecast_demand'],1),
                 'Safety Stock':round(x['safety_stock'],1),'Recommended Order':round(x['recommended_order'],1),
                 'Unit':x['unit'],'Risk':x['risk_level'],'Supplier':s.get('supplier','—'),
                 'Lead Time':f"{s.get('lead_time_days','—')} day(s)",'On-time %':s.get('on_time_pct','—')})
df=pd.DataFrame(data)
a,b,c=st.columns(3)
a.metric('Items to Reorder',int((df['Recommended Order']>0).sum()))
b.metric('Items to Hold/Reduce',int((df['Recommended Order']==0).sum()))
c.metric('High Expiry Risk',int((df['Risk']=='HIGH').sum()))
st.dataframe(df.sort_values('Recommended Order',ascending=False),use_container_width=True,hide_index=True)
st.info('Decision rule is transparent: forecast demand + ~1.5 days safety stock − current usable inventory. Supplier lead time is surfaced for procurement context.')
