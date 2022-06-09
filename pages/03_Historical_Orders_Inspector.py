import streamlit as st

from data_fetchers import historical_table, fills_table, auctions_table

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
else:
    st.stop()

if order_grid["selected_rows"]:
    st.caption("Selected order:")
    st.json(order_grid["selected_rows"][0])

    st.subheader("Auctions")
    auctions_table(order_grid["selected_rows"][0]["OrderHash"])
    st.subheader("Order Fills")
    fills_grid = fills_table(order_grid["selected_rows"][0]["OrderHash"])

    if len(fills_grid[0]) > 0:
        if fills_grid[0]["selected_rows"]:
            st.caption("Selected fill:")
            st.write(fills_grid[0]["selected_rows"][0])
            st.markdown("[Etherscan (Transaction)](https://etherscan.io/tx/" + fills_grid[0]["selected_rows"][0][
                "txHash"] + ")",
                        unsafe_allow_html=True)
            st.markdown(
                "[EigenPhi](https://eigenphi.io/ethereum/tx/" + fills_grid[0]["selected_rows"][0]["txHash"] + ")",
                unsafe_allow_html=True)
