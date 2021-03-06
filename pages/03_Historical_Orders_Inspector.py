import streamlit as st

from data_fetchers import historical_table, fills_table, auctions_table, known_address_fetch

st.set_page_config(page_title="Historical Order Viewer", page_icon="🤖", layout="wide")
st.markdown('<h1 align="center">Historical Orders</h1>', unsafe_allow_html=True)

wallet_address = st.text_input("Wallet Address / Identifier", "")

if len(wallet_address) > 0:
    if wallet_address[:2] != "0x":
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
else:
    st.stop()

if order_grid["selected_rows"]:
    st.caption("Selected order:")
    st.json(order_grid["selected_rows"][0])

    auctions_header = st.container()
    auctions_grid, _ = auctions_table(order_grid["selected_rows"][0]["OrderHash"])
    if len(auctions_grid) > 0:
        auctions_header.markdown('<h3 align="center">Auctions</h3>', unsafe_allow_html=True)
        if auctions_grid["selected_rows"]:
            st.caption("Selected auction:")
            st.write(auctions_grid["selected_rows"][0])
    else:
        st.stop()

    fills_header = st.container()
    fills_grid, _ = fills_table(order_grid["selected_rows"][0]["OrderHash"])
    if len(fills_grid) > 0:
        fills_header.markdown('<h3 align="center">Order Fills</h3>', unsafe_allow_html=True)
        if fills_grid["selected_rows"]:
            st.caption("Selected fill:")
            st.write(fills_grid["selected_rows"][0])
            st.markdown("[Etherscan (Transaction)](https://etherscan.io/tx/" + fills_grid["selected_rows"][0][
                "txHash"] + ")",
                        unsafe_allow_html=True)
            st.markdown(
                "[EigenPhi](https://eigenphi.io/ethereum/tx/" + fills_grid["selected_rows"][0]["txHash"] + ")",
                unsafe_allow_html=True)
