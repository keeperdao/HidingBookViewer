import streamlit as st
import altair as alt
from data_fetchers import price_fetch
import pandas as pd


def price_chart(token1, token2, lookback, target):
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
                alt.Tooltip("Timestamp", title="Date", format="%m/%d/%y %H:%m"),
                alt.Tooltip("Close", title="Price (" + token1 + "/" + token2 + ")"),
            ],
        )
        .add_selection(hover)
    )

    price_target = base.mark_rule().encode(
        y='Target',
        size=alt.value(2)
    )

    st.altair_chart((line + points + price_target + tooltips), use_container_width=True)
    with st.expander("Legend"):
        st.markdown('<p style="color: SteelBlue; font-weight: bold">― Historical Price</p>', unsafe_allow_html=True)
        st.markdown('<p style="color: Black; font-weight: bold">― Limit Price</p>', unsafe_allow_html=True)
        st.write('Note: all times are in UTC')


def size_pie_chart(order_data):
    order_data["size_group"] = "Empty"
    order_data['TakerAmtUSD'] = pd.to_numeric(order_data['TakerAmtUSD'])
    order_data.loc[order_data['TakerAmtUSD'] < 1000, "size_group"] = "A. Tiny (<$1k)"
    order_data.loc[
        (1000 <= order_data['TakerAmtUSD']) & (order_data['TakerAmtUSD'] < 5000), "size_group"] = "B. Small ($1k-$5k)"
    order_data.loc[
        (5000 <= order_data['TakerAmtUSD']) & (order_data['TakerAmtUSD'] < 10000), "size_group"] = "C. Avg ($5k-$10k)"
    order_data.loc[
        (10000 <= order_data['TakerAmtUSD']) & (
                order_data['TakerAmtUSD'] < 50000), "size_group"] = "D. Large ($10k-$50k)"
    order_data.loc[(50000 <= order_data['TakerAmtUSD']) & (
            order_data['TakerAmtUSD'] < 150000), "size_group"] = "E. Very Large ($50k-$150k)"
    order_data.loc[order_data['TakerAmtUSD'] >= 150000, 'size_group'] = "F. Huge (>$150k)"

    order_stats = order_data['size_group'].value_counts()
    order_stats = order_stats.reset_index()

    base = alt.Chart(order_stats).encode(
        theta=alt.Theta("size_group:Q", stack=True),
        color=alt.Color("index:N", legend=alt.Legend(title="Order Size"))
    )
    pie = base.mark_arc(outerRadius=100)
    label = base.mark_text(radius=120, size=14).encode(text="size_group:Q")

    st.altair_chart(pie + label)

    return order_data


def hiding_book_depth(order_data, mode="Token"):
    order_data['MakerAmtUSD'] = pd.to_numeric(order_data['MakerAmtUSD'])
    order_data['TakerAmtUSD'] = pd.to_numeric(order_data['TakerAmtUSD'])
    if mode == "Token":
        maker_agg_data = order_data.groupby(['MakerToken']).sum().reset_index().rename(
            columns={'MakerToken': 'Token'})
        taker_agg_data = order_data.groupby(['TakerToken']).sum().reset_index().rename(
            columns={'TakerToken': 'Token'})
        overlap = taker_agg_data['Token'].isin(maker_agg_data['Token'])
        unique_taker_data = taker_agg_data[~overlap].drop(columns=['OrderSalt', 'MakerAmtUSD'])
        unique_taker_data = unique_taker_data.rename(columns={'TakerAmtUSD': 'TotalTakerUSD'})

        order_data = pd.DataFrame(maker_agg_data.loc[:, ['Token', 'MakerAmtUSD']]).rename(
            columns={'MakerAmtUSD': 'TotalMakerUSD'})

        taker_agg_data = taker_agg_data.set_index("Token")
        order_data['TotalTakerUSD'] = order_data['Token'].map(taker_agg_data['TakerAmtUSD']).fillna(0)

        unique_taker_data['TotalMakerUSD'] = 0
        order_data = pd.concat([order_data, unique_taker_data])
        order_data = order_data.rename(columns={'TotalTakerUSD': 'Taker', 'TotalMakerUSD': 'Maker'})

        chart = alt.Chart(order_data).mark_bar(clip=True).encode(
            x=alt.X('ValueUSD:Q', scale=alt.Scale(domain=(0, 10000000)), axis=alt.Axis(labelAngle=-45)),
            y='Direction:N',
            color=alt.Color('Direction:N', legend=None),
            row=alt.Row('Token:N'),
            tooltip=[alt.Tooltip('Token:N'), alt.Tooltip('Direction:N'), alt.Tooltip('ValueUSD:Q', format='$,.2f')]
        ).transform_fold(
            as_=['Direction', 'ValueUSD'],
            fold=['Taker', 'Maker']
        )
    else:
        order_data['MakerToken'] = order_data['MakerToken'].astype('category')
        order_data['TakerToken'] = order_data['TakerToken'].astype('category')

        agg_data = order_data.groupby(['MakerToken', 'TakerToken']).sum().reset_index().drop(
            columns=['OrderSalt'])

        combined_data = pd.DataFrame(columns={'Pair', 'MakerToken', 'TakerToken', 'SellValueUSD', 'BuyValueUSD'}). \
            rename({"SellValueUSD: MakerValueUSD", "BuyValueUSD: TakerValueUSD"})
        for _, row in agg_data.iterrows():
            pair = row['MakerToken'] + '/' + row["TakerToken"]
            inverse = row['TakerToken'] + '/' + row["MakerToken"]
            value = row['MakerAmtUSD']
            if value != 0:
                matched_idx = combined_data.index[combined_data['Pair'] == inverse]
                if len(matched_idx) > 0:
                    combined_data.loc[matched_idx[0], 'TakerValueUSD'] = value
                else:
                    combined_data = combined_data.append({'Pair': pair, 'MakerToken': row['MakerToken'],
                                                          'TakerToken': row['TakerToken'], 'TakerValueUSD': 0,
                                                          'MakerValueUSD': value}, ignore_index=True)
        combined_data = combined_data.rename(columns={'TakerValueUSD': 'Taker', 'MakerValueUSD': 'Maker'})
        combined_data.set_index('Pair')

        chart = alt.Chart(combined_data).mark_bar(clip=True).encode(
            x=alt.X('ValueUSD:Q', scale=alt.Scale(domain=(0, 5000000)), axis=alt.Axis(labelAngle=-45)),
            y='Direction:N',
            color=alt.Color('Direction:N', legend=None),
            row=alt.Row('Pair:N'),
            tooltip=[alt.Tooltip('Pair:N'), alt.Tooltip('Direction:N'), alt.Tooltip('ValueUSD:Q', format='$,.2f')]
        ).transform_fold(
            as_=['Direction', 'ValueUSD'],
            fold=['Maker', 'Taker']
        )

    st.altair_chart(chart)


def order_history_chart(data):
    points = alt.Chart(data).mark_circle().encode(
        x=alt.Y('Expiry:T', axis=alt.Y(title="Expiry (UTC)")),
        y=alt.Y('MakerAmtUSD:Q'),
        color=alt.Color('FillPct:Q', scale=alt.Scale(scheme='redyellowgreen')),
        tooltip=[alt.Tooltip('Created:T', format="%m/%d/%y %H:%m"), alt.Tooltip('Expiry:T', format="%m/%d/%y %H:%m"),
                 alt.Tooltip('MakerToken:N'), alt.Tooltip('MakerAmt:Q'),
                 alt.Tooltip('TakerToken:N'), alt.Tooltip('TakerAmt:Q'),
                 alt.Tooltip('FillPct:Q')]
    )

    st.altair_chart(points, use_container_width=True)
