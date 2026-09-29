import streamlit as st, pandas as pd
from services.db import init_db
from services.inventory import batches,status,days_left
from services.qr import make_qr
init_db(); st.title('📋 Batch Inventory')
rows=batches()
if rows:
    df=pd.DataFrame(rows); df['status']=df.expiry_date.map(status); df['days_left']=df.expiry_date.map(days_left); df['inventory_value']=df.qty*df.unit_cost
    st.dataframe(df[['batch_id','ingredient','supplier','qty','unit','unit_cost','expiry_date','days_left','status','inventory_value']],use_container_width=True,hide_index=True)
    selected=st.selectbox('Generate / View Batch QR',[b['batch_id'] for b in rows]); b=next(x for x in rows if x['batch_id']==selected); st.image(make_qr(b),width=180)
else: st.info('No stock available.')
