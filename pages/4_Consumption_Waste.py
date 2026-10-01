import streamlit as st
import pandas as pd
from services.db import init_db
from services.inventory import batches, fefo, consume_fefo, transact, transaction_history

init_db()
st.title('🍳 Consumption & Waste')
st.caption('Consumption can be automatically allocated using FEFO. Waste remains batch-specific for traceability.')
rows = batches()
if not rows:
    st.info('No available stock.'); st.stop()

tab1, tab2, tab3 = st.tabs(['🍽️ Record Consumption','🗑️ Record Waste','🕘 Transaction History'])

with tab1:
    usable = [b for b in rows if any(x['batch_id']==b['batch_id'] for x in fefo(b['ingredient']))]
    ingredients = sorted(set(b['ingredient'] for b in usable))
    if not ingredients:
        st.warning('No non-expired stock is available for consumption.')
    else:
        ing = st.selectbox('Ingredient', ingredients, key='consume_ing')
        candidates = fefo(ing)
        total = sum(b['qty'] for b in candidates)
        unit = candidates[0]['unit']
        first = candidates[0]
        st.info(f"FEFO will use **{first['batch_id']} first** · expires {first['expiry_date']} · {first['qty']:g} {unit} currently available in that batch.")
        qty = st.number_input(f'Quantity consumed ({unit})', min_value=0.1, max_value=float(total), value=min(1.0,float(total)), step=0.1)
        if st.button('Record Consumption with FEFO', type='primary'):
            try:
                allocations = consume_fefo(ing, qty)
                st.success(f'Recorded {qty:g} {unit} of {ing}. Inventory updated using FEFO.')
                st.dataframe(pd.DataFrame(allocations), use_container_width=True, hide_index=True)
                st.rerun()
            except ValueError as e: st.error(str(e))

with tab2:
    labels = {f"{b['batch_id']} — {b['ingredient']} — {b['qty']:g} {b['unit']}":b for b in rows}
    label = st.selectbox('Batch', labels, key='waste_batch'); b = labels[label]
    qty = st.number_input(f"Quantity wasted ({b['unit']})",0.1,float(b['qty']),min(1.0,float(b['qty'])),step=0.1)
    reason = st.selectbox('Waste reason',['Spoiled','Expired','Prep waste','Damaged','Quality rejection','Other'])
    st.caption(f"Estimated waste value: ₹{qty*b['unit_cost']:,.0f}")
    if st.button('Record Waste',type='primary'):
        try:
            transact(b['batch_id'],'Waste',qty,reason)
            st.success('Waste recorded. Inventory and dashboard metrics updated.')
            st.rerun()
        except ValueError as e: st.error(str(e))

with tab3:
    tx = pd.DataFrame(transaction_history(100))
    if tx.empty: st.info('No transactions yet.')
    else:
        tx['value'] = tx['value'].fillna(0)
        st.dataframe(tx[['created_at','type','ingredient','batch_id','qty','unit','reason','value']],use_container_width=True,hide_index=True)
