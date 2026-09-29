import streamlit as st, pandas as pd
from services.db import init_db
from services.inventory import batches,fefo,days_left
init_db(); st.title('⏳ FEFO — Use First')
items=sorted(set(b['ingredient'] for b in batches()))
if not items: st.info('No inventory available.'); st.stop()
ing=st.selectbox('Ingredient',items); rows=fefo(ing)
if rows:
    first=rows[0]; st.error(f"🔴 USE FIRST — {first['batch_id']} | {first['qty']} {first['unit']} remaining | expires in {days_left(first['expiry_date'])} day(s) | ₹{first['qty']*first['unit_cost']:,.0f} value")
    st.dataframe(pd.DataFrame(rows)[['batch_id','qty','unit','expiry_date','supplier']],use_container_width=True,hide_index=True)
else: st.warning('All remaining batches are expired.')
