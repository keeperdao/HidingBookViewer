import streamlit as st

from data_fetchers import historical_table, order_table, fills_table, auctions_table, order_string
from charts import price_chart

if __name__ == '__main__':
    st.set_page_config(page_title="Hiding Book Viewer", page_icon="🤖")
    st.title('Rook Hiding Book Viewer')

    table = st.radio("Order type", ("Open Orders", "Past Orders"))

    if table == "Open Orders":
        st.subheader("Open Orders")
        order_grid, order_data = order_table()
        if len(order_grid) == 0:
            st.stop()
    else:
        st.subheader("Past Orders")
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

        if table == "Open Orders":
            lookback = st.radio("Lookback", ("1D", "1W", "1M", "1Y", "MAX"), horizontal=True)
            price_chart(order_grid["selected_rows"][0]["MakerToken"],
                        order_grid["selected_rows"][0]["TakerToken"],
                        lookback,
                        order_grid["selected_rows"][0]["TakerAmt"] / order_grid["selected_rows"][0]["MakerAmt"],
                        order_grid["selected_rows"][0]["Created"],
                        order_grid["selected_rows"][0]["Expiry"])
            order_string(order_grid["selected_rows"][0])
            st.markdown(
                "[Etherscan (Wallet)](https://etherscan.io/address/" + order_grid["selected_rows"][0][
                    "Address"] + "#tokentxns)",
                unsafe_allow_html=True)
            st.markdown(
                "[Nansen Wallet Profiler](https://pro.nansen.ai/wallet-profiler?address=" +
                order_grid["selected_rows"][0][
                    "Address"] + ")",
                unsafe_allow_html=True)
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
