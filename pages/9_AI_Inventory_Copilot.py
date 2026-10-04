import streamlit as st
from services.db import init_db
from services.intelligence import answer_copilot
init_db(); st.title('🤖 AI Inventory Copilot')
st.caption('Grounded decision assistant: inventory/forecast services calculate the numbers; the copilot explains the results.')
st.warning('POC note: this version demonstrates grounded tool-style reasoning without calling an external LLM API. No inventory numbers are invented by a language model.')
examples=['What should I use first?','What should I order?','Why is an ingredient high risk?']
q=st.text_input('Ask FreshFlow',placeholder='e.g. What should I order?')
cols=st.columns(3)
for i,e in enumerate(examples):
    if cols[i].button(e,use_container_width=True): q=e
if q:
    st.markdown('### FreshFlow response')
    st.success(answer_copilot(q))
    st.caption('Grounded in current batch inventory + forecast + expiry-risk + supplier data.')
