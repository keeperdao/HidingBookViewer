import streamlit as st

from data_fetchers import order_table
from charts import size_pie_chart, hiding_book_depth

st.set_page_config(page_title="Open Order Viewer", page_icon="🤖", layout="wide")
st.markdown('<h1 align="center">Open Orders</h1>', unsafe_allow_html=True)

order_grid, order_data = order_table()
if len(order_grid) == 0:
    st.stop()
size_pie_chart(order_grid["data"])

col1, col2 = st.columns(2)
with col1:
    hiding_book_depth(order_grid["data"], "Token")
with col2:
    hiding_book_depth(order_grid["data"], "Pair")
