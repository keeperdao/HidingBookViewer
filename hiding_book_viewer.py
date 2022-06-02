import streamlit as st

from data_fetchers import historical_table, order_table, fills_table, auctions_table

if __name__ == '__main__':
    st.set_page_config(page_title="Hiding Book Viewer", page_icon="🤖")
    st.title('Rook Hiding Book Viewer')

    table = st.radio("Order type", ("Open Orders", "Past Orders"))

    if table == "Open Orders":
        st.subheader("Open Orders")
        order_grid = order_table()
        if len(order_grid) == 0:
            st.stop()
    else:
        st.subheader("Past Orders (100 most recent)")
        wallet_address = st.text_input("Wallet Address", "")

        if len(wallet_address) > 0:
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

        if len(fills_grid) > 0:
            if fills_grid["selected_rows"]:
                st.caption("Selected fill:")
                st.write(fills_grid["selected_rows"][0])
                st.markdown("[Etherscan](https://etherscan.io/tx/" + fills_grid["selected_rows"][0]["txHash"] + ")",
                            unsafe_allow_html=True)
                st.markdown(
                    "[EigenPhi](https://eigenphi.io/ethereum/tx/" + fills_grid["selected_rows"][0]["txHash"] + ")",
                    unsafe_allow_html=True)
