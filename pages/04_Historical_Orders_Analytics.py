import streamlit as st

from data_fetchers import historical_table, fills_table, auctions_table
from charts import size_pie_chart

st.set_page_config(page_title="Historical Order Viewer", page_icon="🤖")
st.title('Historical Orders')

wallet_address = st.text_input("Wallet Address", "")

if len(wallet_address) > 0:
    st.markdown(
        "[Etherscan (Wallet)](https://etherscan.io/address/" + wallet_address + "#tokentxns)",
        unsafe_allow_html=True)
    st.markdown(
        "[Nansen Wallet Profiler](https://pro.nansen.ai/wallet-profiler?address=" + wallet_address + ")",
        unsafe_allow_html=True)
    order_grid = historical_table(wallet_address)
    if len(order_grid) > 0:
        size_pie_chart(order_grid["data"])
    else:
        st.stop()
else:
    st.stop()

if order_grid["selected_rows"]:
    st.caption("Selected order:")
    st.json(order_grid["selected_rows"][0])

    st.subheader("Auctions")
    auctions_grid, _ = auctions_table(order_grid["selected_rows"][0]["OrderHash"])
    if len(auctions_grid) > 0:
        if auctions_grid["selected_rows"]:
            st.caption("Selected auction:")
            st.write(auctions_grid[0]["selected_rows"][0])

    st.subheader("Order Fills")
    fills_grid, _ = fills_table(order_grid["selected_rows"][0]["OrderHash"])

    if len(fills_grid) > 0:
        if fills_grid["selected_rows"]:
            st.caption("Selected fill:")
            st.write(fills_grid["selected_rows"][0])
            st.markdown("[Etherscan (Transaction)](https://etherscan.io/tx/" + fills_grid["selected_rows"][0][
                "txHash"] + ")",
                        unsafe_allow_html=True)
            st.markdown(
                "[EigenPhi](https://eigenphi.io/ethereum/tx/" + fills_grid["selected_rows"][0]["txHash"] + ")",
                unsafe_allow_html=True)
