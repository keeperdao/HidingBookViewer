import streamlit as st
import altair as alt
from data_fetchers import price_fetch
from datetime import datetime


def price_chart(token1, token2, lookback, target, creation, expiry):
    prices1 = price_fetch(token1, lookback)
    prices2 = price_fetch(token2, lookback)

    prices1.set_index('Timestamp')
    prices2.set_index('Timestamp')

    prices = prices1
    prices["Close"] = prices1["Close"].div(prices2["Close"])
    prices["Target"] = target

    base = alt.Chart(prices).properties(width=550)

    hover = alt.selection_single(
        fields=["Timestamp"],
        nearest=True,
        on="mouseover",
        empty="none",
    )

    line = base.mark_line().encode(
        alt.X('Timestamp:T'),
        alt.Y('Close:Q', scale=alt.Scale(zero=False))
    )

    points = line.transform_filter(hover).mark_point(size=65)

    tooltips = (
        alt.Chart(prices)
        .mark_rule()
        .encode(
            x="Timestamp",
            y="Close",
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("Timestamp", title="Date"),
                alt.Tooltip("Close", title="Price (" + token1 + "/" + token2 + ")"),
            ],
        )
        .add_selection(hover)
    )

    price_target = base.mark_rule().encode(
        y='Target',
        size=alt.value(2)
    )

    expiry = datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%S")
    if prices["Timestamp"].iloc[0] < expiry <= datetime.utcnow():
        expiry_line = base.mark_rule().encode(x=alt.datum(alt.DateTime(
            year=expiry.year, month=expiry.month, date=expiry.day, hours=expiry.hour, minutes=expiry.minute,
            seconds=expiry.second)))
    else:
        expiry_line = []

    creation = datetime.strptime(creation, "%Y-%m-%dT%H:%M:%S")
    if prices["Timestamp"].iloc[0] < creation:
        creation_line = base.mark_rule().encode(x=alt.datum(alt.DateTime(
            year=creation.year, month=creation.month, date=creation.day, hours=creation.hour,
            minutes=creation.minute,
            seconds=creation.second)))
    else:
        creation_line = []

    if expiry_line:
        if creation_line:
            st.altair_chart((line + points + price_target + tooltips + creation_line + expiry_line),
                            use_container_width=True)
        else:
            st.altair_chart((line + points + price_target + tooltips + expiry_line), use_container_width=True)
    else:
        if creation_line:
            st.altair_chart((line + points + price_target + creation_line + tooltips), use_container_width=True)
        else:
            st.altair_chart((line + points + price_target + tooltips), use_container_width=True)
