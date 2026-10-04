import streamlit as st,pandas as pd,plotly.express as px
from services.db import init_db
from services.intelligence import all_snapshots
init_db(); st.title('🎛️ Scenario Simulator')
st.caption('See how demand changes affect purchasing and expiry decisions.')
pct=st.slider('Expected demand change',-30,60,20,5)
mult=1+pct/100
base=all_snapshots(7,1.0); scen=all_snapshots(7,mult)
rows=[]
for a,b in zip(base,scen):
    rows.append({'Ingredient':a['ingredient'],'Base Demand':a['forecast_demand'],'Scenario Demand':b['forecast_demand'],
                 'Base Order':a['recommended_order'],'Scenario Order':b['recommended_order'],'Unit':a['unit']})
df=pd.DataFrame(rows)
st.plotly_chart(px.bar(df.melt('Ingredient',value_vars=['Base Order','Scenario Order'],var_name='Plan',value_name='Order Qty'),
                       x='Ingredient',y='Order Qty',color='Plan',barmode='group'),use_container_width=True)
st.dataframe(df.round(1),use_container_width=True,hide_index=True)
