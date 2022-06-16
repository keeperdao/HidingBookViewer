import streamlit as st

from data_fetchers import order_table, fills_table, auctions_table, order_string
from charts import price_chart, size_pie_chart, hiding_book_depth

st.set_page_config(page_title="Open Order Viewer", page_icon="🤖")
st.title('Open Orders')

order_grid, order_data = order_table()
if len(order_grid) == 0:
    st.stop()
# size_pie_chart(order_grid["data"])
# hiding_book_depth(order_grid["data"])

if order_grid["selected_rows"]:
    st.caption("Selected order:")

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
    auctions_grid, _ = auctions_table(order_grid["selected_rows"][0]["OrderHash"])
    if len(auctions_grid) > 0:
        if auctions_grid["selected_rows"]:
            st.caption("Selected auction:")
            st.write(auctions_grid["selected_rows"][0])

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
