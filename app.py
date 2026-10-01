import streamlit as st
from services.db import init_db
init_db()
st.set_page_config(page_title='FreshFlow AI',page_icon='🌿',layout='wide')
st.title('🌿 FreshFlow AI')
st.subheader('Intelligent Perishable Inventory & Food Waste Management')
st.info('POC: Batch traceability → FEFO → Live Operations → Predictive Expiry Risk → Demand & Purchase Recommendations')
st.markdown('Use the pages in the sidebar to run the end-to-end restaurant inventory workflow.')
