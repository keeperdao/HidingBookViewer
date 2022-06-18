import streamlit as st

from data_fetchers import order_table
from charts import size_pie_chart, hiding_book_depth

st.set_page_config(page_title="Open Order Viewer", page_icon="🤖", layout="wide")
st.markdown('<h1 align="center">Open Orders</h1>', unsafe_allow_html=True)

order_grid, order_data = order_table()
if len(order_grid) == 0:
    st.stop()
st.markdown('<h3 align="center">Order Size Breakdown</h3>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.write("")
with col2:
    size_pie_chart(order_grid["data"])
with col3:
    st.write("")

st.markdown('<h3 align="center">Order Book Depth</h3>', unsafe_allow_html=True)
col4, col5 = st.columns(2)
with col4:
    hiding_book_depth(order_grid["data"], "Token")
with col5:
    hiding_book_depth(order_grid["data"], "Pair")
