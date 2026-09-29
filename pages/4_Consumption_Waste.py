import streamlit as st
from services.db import init_db
from services.inventory import batches,transact
init_db(); st.title('🍳 Consumption & Waste')
rows=batches()
if not rows: st.info('No available stock.'); st.stop()
labels={f"{b['batch_id']} — {b['ingredient']} — {b['qty']} {b['unit']}":b for b in rows}; label=st.selectbox('Batch',labels); b=labels[label]
kind=st.radio('Transaction',['Consumption','Waste'],horizontal=True); qty=st.number_input(f"Quantity ({b['unit']})",0.1,float(b['qty']),min(1.0,float(b['qty'])))
reason=st.selectbox('Waste reason',['Spoiled','Expired','Prep waste','Damaged','Other']) if kind=='Waste' else ''
if st.button('Record Transaction',type='primary'):
    try: transact(b['batch_id'],kind,qty,reason); st.success(f'{kind} recorded. Inventory updated.'); st.rerun()
    except ValueError as e: st.error(str(e))
