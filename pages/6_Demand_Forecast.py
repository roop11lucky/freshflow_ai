import streamlit as st, pandas as pd, plotly.express as px
from services.db import init_db
from services.inventory import batches
from services.forecasting import history,forecast,evaluate_models
init_db()
st.title('📈 Demand Forecast')
st.caption('120-day demand history → backtested baseline models → 7-day forecast.')
ings=sorted(set(b['ingredient'] for b in batches()))
ing=st.selectbox('Ingredient',ings)
ev=evaluate_models(ing); hist=pd.DataFrame(history(ing,120)); fc=pd.DataFrame(forecast(ing,7))
c1,c2,c3=st.columns(3)
c1.metric('Selected Model',ev['selected'])
c2.metric('Backtest MAE',f"{ev['mae']:.2f}" if ev['mae'] is not None else 'N/A')
c3.metric('Backtest MAPE',f"{ev['mape']:.1f}%" if ev['mape'] is not None else 'N/A')
if not hist.empty:
    hist=hist.rename(columns={'demand_date':'Date','qty':'Quantity'}); hist['Series']='Historical'
    f=fc.rename(columns={'date':'Date','forecast':'Quantity'}); f['Series']='Forecast'
    chart=pd.concat([hist[['Date','Quantity','Series']].tail(45),f[['Date','Quantity','Series']]])
    st.plotly_chart(px.line(chart,x='Date',y='Quantity',color='Series',markers=True),use_container_width=True)
st.subheader('Model Evaluation')
st.dataframe(pd.DataFrame(ev['models']).rename(columns={'model':'Model','mae':'MAE','mape':'MAPE %'}),use_container_width=True,hide_index=True)
st.caption('POC history is deterministic simulated POS demand and is labelled as such. Replace demand_history with real POS data in production.')
