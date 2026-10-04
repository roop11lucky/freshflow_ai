import streamlit as st,pandas as pd,plotly.express as px
from services.db import init_db
from services.intelligence import all_snapshots,ingredient_snapshot
init_db(); st.title('⚠️ Expiry Risk')
st.caption('Explainable 0–100 score combining expiry urgency, predicted excess and perishability.')
rows=all_snapshots()
df=pd.DataFrame([{k:v for k,v in x.items() if k not in ('forecast','model','supplier')} for x in rows])
st.plotly_chart(px.bar(df.sort_values('risk_score',ascending=False),x='ingredient',y='risk_score',color='risk_level',
                       labels={'ingredient':'Ingredient','risk_score':'Risk Score','risk_level':'Risk'}),use_container_width=True)
ing=st.selectbox('Inspect ingredient',df.ingredient.tolist()); x=ingredient_snapshot(ing)
a,b,c,d=st.columns(4)
a.metric('Expiry Risk',f"{x['risk_score']}/100")
b.metric('Level',x['risk_level']); c.metric('Predicted Excess',f"{x['predicted_excess']:.1f} {x['unit']}")
d.metric('Potential Exposure',f"₹{x['value_at_risk']:,.0f}")
st.progress(x['risk_score']/100)
st.markdown(f"""**Why this score?**  
Earliest expiry: **{x['earliest_expiry_days']} day(s)** · Forecast consumption: **{x['daily_demand']:.1f} {x['unit']}/day** ·
Current stock: **{x['stock']:.1f} {x['unit']}**. The score is intentionally explainable rather than a black-box probability.""")
