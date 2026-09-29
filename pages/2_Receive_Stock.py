import streamlit as st
from datetime import date,timedelta
from services.db import init_db
from services.inventory import add_batch
from services.qr import make_qr
init_db(); st.title('📦 Receive Stock')
with st.form('receive'):
    c1,c2=st.columns(2); ingredient=c1.text_input('Ingredient','Chicken Breast'); supplier=c2.text_input('Supplier','ABC Foods')
    c1,c2,c3=st.columns(3); batch=c1.text_input('Batch ID'); qty=c2.number_input('Quantity',0.1,10000.0,10.0); unit=c3.selectbox('Unit',['kg','L','units'])
    c1,c2,c3=st.columns(3); cost=c1.number_input('Unit Cost (₹)',0.0,100000.0,400.0); received=c2.date_input('Received Date',date.today()); expiry=c3.date_input('Expiry Date',date.today()+timedelta(days=7))
    submit=st.form_submit_button('Receive Inventory',type='primary')
if submit:
    if not batch.strip(): st.error('Batch ID is required.')
    elif expiry < received: st.error('Expiry date cannot be before received date.')
    else:
        try:
            add_batch((batch.strip(),ingredient.strip(),supplier.strip(),qty,qty,unit,cost,received.isoformat(),expiry.isoformat()))
            st.success(f'Batch {batch} received successfully.')
            obj={'batch_id':batch,'ingredient':ingredient,'expiry_date':expiry.isoformat()}; st.image(make_qr(obj),width=180,caption=f'QR — {batch}')
        except Exception as e: st.error(f'Could not receive stock: {e}')
