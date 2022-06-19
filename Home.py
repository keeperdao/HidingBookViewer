import streamlit as st

if __name__ == '__main__':
    st.set_page_config(page_title="Rook Order Viewer", page_icon="🤖")
    st.markdown('<h1 align="center">Rook Order Viewer</h1>', unsafe_allow_html=True)

    st.write("This app provides a means to view both current Hiding Book orders as well as past orders\
        that have been submitted by Rook users.")
    st.write("It is broken down into four sections:")
    st.markdown("- **Open Orders Inspector**: This page provides a table (with filtering and sorting) of all\
        current HidingBook orders and allows viewing of associated auctions and fills each order.")
    st.markdown("- **Open Orders Analytics**: This page provides charts showing breakdown of open Hiding Book orders by size\
        as well as buy and sell depth at both a token and pair level.")
    st.markdown("- **Historical Orders Inspector**: This page provides a table (with filtering and sorting) of all\
        orders from a given wallet and allows viewing of associated auctions and fills each order.")
    st.markdown("- **Historical Orders Analytics**: This page provides charts showing a user's past orders over time, by size\
        and fill level.")

    st.markdown('<h4>General tips</h4>', unsafe_allow_html=True)
    st.markdown("- You can access the app's setting on the top right. The app is best suited for\
        **Wide mode** with a **Light** or **Custom** theme.")
    st.markdown("- The app can be reset from the settings menu or by pressing 'R.'")
    st.markdown("- The app cache can be cleared from the settings menu or by pressing 'C.'")
    st.markdown("- Logging can be accessed via 'Manage app' at the bottom right of the app.")
    st.markdown("- The sidebar can be closed to increase width available.")
    st.markdown("- **Filters** are available for all tables from the right sidebar. Additional table columns can be shown\
                from the **Columns** tab.")
    st.markdown("- Copying is not available in all tables. In these cases, data can be copied from provided JSON data.")
