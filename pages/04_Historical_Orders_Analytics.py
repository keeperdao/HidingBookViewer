import streamlit as st

from data_fetchers import historical_table, known_address_fetch
from charts import size_pie_chart, order_history_chart

st.set_page_config(page_title="Historical Order Viewer", page_icon="🤖", layout="wide")
st.markdown('<h1 align="center">Historical Orders</h1>', unsafe_allow_html=True)

wallet_address = st.text_input("Wallet Address / Identifier", "")

if len(wallet_address) > 0:
    if wallet_address[:1] != "0x":
        known_addresses = known_address_fetch()
        wallet_address = known_addresses[known_addresses["Name"] == wallet_address].index.values[0]
        st.write("Wallet address: " + wallet_address)

    st.markdown(
        "[Etherscan (Wallet)](https://etherscan.io/address/" + wallet_address + "#tokentxns)",
        unsafe_allow_html=True)
    st.markdown(
        "[Nansen Wallet Profiler](https://pro.nansen.ai/wallet-profiler?address=" + wallet_address + ")",
        unsafe_allow_html=True)
    try:
        order_grid = historical_table(wallet_address)
    except:
        st.stop()

    if len(order_grid) > 0:
        order_history_chart(order_grid["data"])
        size_pie_chart(order_grid["data"])
