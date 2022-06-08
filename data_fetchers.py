import streamlit as st
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


@st.experimental_memo()
def market_maker_fetch(start_date=None, end_date=None):
    mm_params = {"startTimestamp": start_date, "endTimestamp ": end_date}
    mm_json = requests.get("https://api.rook.fi/api/v1/coordinator/marketMakers", params=mm_params).json()
    mm_data = pd.json_normalize(mm_json, meta=["name"], record_path=["makerAddresses"])

    mm_data = mm_data.rename(columns={"name": "Name", mm_data.columns[0]: "Address"}).set_index("Address")
    mm_data["Type"] = "Market Maker"

    return mm_data


@st.experimental_memo()
def keeper_fetch(start_date=None, end_date=None):
    keeper_params = {"startTimestamp": start_date, "endTimestamp ": end_date}
    keeper_json = requests.get("https://api.rook.fi/api/v1/coordinator/keepers", params=keeper_params).json()
    keeper_data = pd.json_normalize(keeper_json, meta=["name"], record_path=["activeTakerAddresses"])

    keeper_data = keeper_data.rename(columns={"name": "Name", keeper_data.columns[0]: "Address"}).set_index("Address")
    keeper_data["Type"] = "Keeper"

    return keeper_data


@st.experimental_memo()
def known_address_fetch(start_date=None, end_date=None):
    mm_data = market_maker_fetch(start_date, end_date)
    keeper_data = keeper_fetch(start_date, end_date)
    other_list = [
        ["hellø.eth", "0x759a159d78342340ebacffb027c05910c093f430"],
        ["3 Arrows Capital", "0xd80856b01feed61e954cd365861bd87e5d39f2e7"],
        ["Amber", "0x5d45594917a30182ca6cfd946b969c1341127c2d"],
        ["one-decade on OpenSea", "0x3765ea1a0d34d9c7991181824d2410fd8612f474"],
        ["Polychain", "0xf286bb612e219916f8e9ba7200bf09ed218890cb"],
        ["Maven11", "0xfacf46ea1e0ad2681103e726f64cfc503e9da5d6"],
        ["Rook Test Wallet", "0x4f72f7Ca2E909BC64022466B46f12Ab328055500"]
    ]
    other_data = pd.DataFrame(other_list, columns=["Name", "Address"]).set_index("Address")
    other_data["Type"] = "User"

    known_data = pd.concat([mm_data, keeper_data, other_data])

    return known_data


@st.experimental_memo(ttl=24 * 60 * 60)
def token_fetch():
    token_json = requests.get("https://api.rook.fi/api/v1/trade/tokens").json()
    token_data = pd.json_normalize(token_json)
    token_data = token_data.drop(columns=["active", "latest_price.timestamp",
                                          "trade_info.makerTokenTradeCount", "trade_info.takerTokenTradeCount",
                                          "trade_info.mostRecentTradeTimestamp"])

    return token_data


@st.experimental_memo(ttl=24 * 60 * 60)
def token_table():
    token_data = token_fetch()
    token_options = GridOptionsBuilder.from_dataframe(
        token_data,
        enableRowGroup=True,
        enableValue=True,
        enablePivot=True)
    token_options.configure_side_bar()
    token_options.configure_selection("single")

    token_grid = AgGrid(
        token_data,
        enable_enterprise_modules=True,
        gridOptions=token_options.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED)
    return token_grid


@st.experimental_memo(ttl=60)
def price_fetch(token_symbol, lookback_str):
    token_data = token_fetch()
    coingecko_id = token_data[token_data["name"] == token_symbol.upper()]["coingecko_id"].iloc[0]

    if lookback_str == "1D":
        lookback = 1
    elif lookback_str == "1W":
        lookback = 7
    elif lookback_str == "1M":
        lookback = 30
    elif lookback_str == "1Y":
        lookback = 365
    else:
        lookback = 'max'

    price_params = {"coinGeckoTokenId": coingecko_id.lower(), "days": str(lookback)}
    raw_data = requests.get("https://api.rook.fi/api/v1/trade/tokenPriceHistory", params=price_params).content
    decoded_price_data = raw_data.decode('utf-8').replace("b'", "").replace("'", "")
    price_data = pd.DataFrame(eval(decoded_price_data), columns=["Timestamp", "Open", "High", "Low", "Close"])
    price_data["Timestamp"] = pd.to_datetime(price_data["Timestamp"], unit='ms')
    price_data = price_data.drop(columns=["Open", "High", "Low"])

    return price_data


@st.experimental_memo(ttl=15 * 60)
def historical_fetch(address):
    token_data = token_fetch()

    order_count = 0
    offset = 0
    while order_count >= offset:
        st.write("Start")
        historical_params = {"makerAddresses": address, "limit": 100, "offset": offset}
        historical_json = requests.get("https://api.rook.fi/api/v1/trade/orderHistory",
                                       params=historical_params).json()

        if offset == 0:
            historical_data = pd.json_normalize(historical_json["items"])
        else:
            historical_data = pd.concat([historical_data, pd.json_normalize(historical_json["items"])])

        offset += 100
        order_count = len(historical_data)

    # historical_json = requests.get(
    #     "https://api.rook.fi/api/v1/trade/orderHistory?makerAddresses=" +
    #     address + "&limit=100&offset=0").json()
    # historical_data = pd.json_normalize(historical_json["items"])

    joined_data0 = pd.merge(historical_data, token_data,
                            left_on="order.makerToken",
                            right_on="address")
    joined_data = pd.merge(joined_data0, token_data,
                           left_on="order.takerToken",
                           right_on="address",
                           suffixes=("_maker", "_taker"))
    joined_data["order.makerAmount"] = joined_data["order.makerAmount"] / (10 ** joined_data["decimals_maker"])
    joined_data["order.takerAmount"] = joined_data["order.takerAmount"] / (10 ** joined_data["decimals_taker"])
    joined_data["metaData.filledAmount_takerToken"] = \
        joined_data["metaData.filledAmount_takerToken"] / (10 ** joined_data["decimals_taker"])
    joined_data["metaData.remainingFillableAmount_takerToken"] = \
        joined_data["metaData.remainingFillableAmount_takerToken"] / (10 ** joined_data["decimals_taker"])

    return joined_data


@st.experimental_memo(ttl=15 * 60)
def historical_table(address):
    raw_historical_data = historical_fetch(address)
    historical_data = pd.DataFrame(raw_historical_data["metaData.orderHash"]).rename(
        columns={"metaData.orderHash": "OrderHash"})
    historical_data["OrderSalt"] = raw_historical_data["order.salt"]
    historical_data["Created"] = pd.to_datetime(raw_historical_data["metaData.creation"], unit='s')
    historical_data["Expiry"] = pd.to_datetime(raw_historical_data["order.expiry"], unit='s')
    historical_data["MakerAmt"] = raw_historical_data["order.makerAmount"]
    historical_data["MakerToken"] = raw_historical_data["name_maker"]
    historical_data["MakerAmtUSD"] = raw_historical_data["order.makerAmount"] * raw_historical_data[
        "latest_price.usd_price_maker"]
    historical_data["MakerAmtETH"] = raw_historical_data["order.makerAmount"] * raw_historical_data[
        "latest_price.eth_price_maker"]
    historical_data["TakerAmt"] = raw_historical_data["order.takerAmount"]
    historical_data["TakerToken"] = raw_historical_data["name_taker"]
    historical_data["TakerAmtUSD"] = raw_historical_data["order.takerAmount"] * raw_historical_data[
        "latest_price.usd_price_taker"]
    historical_data["TakerAmtETH"] = raw_historical_data["order.takerAmount"] * raw_historical_data[
        "latest_price.eth_price_taker"]
    historical_data["UnfilledTakerAmt"] = raw_historical_data["metaData.remainingFillableAmount_takerToken"]
    historical_data["UnfilledTakerUSD"] = historical_data["UnfilledTakerAmt"] * raw_historical_data[
        "latest_price.usd_price_taker"]
    historical_data["UnfilledTakerETH"] = historical_data["UnfilledTakerAmt"] * raw_historical_data[
        "latest_price.eth_price_taker"]
    historical_data["FillPct"] = raw_historical_data["metaData.filledAmount_takerToken"] / raw_historical_data[
        "order.takerAmount"]

    historical_options = GridOptionsBuilder.from_dataframe(
        historical_data,
        enableRowGroup=True,
        enableValue=True,
        enablePivot=True)
    historical_options.configure_columns(["Created", "Expiry"], type=["dateColumnFilter", "customDateTimeFormat"],
                                         custom_format_string='MM/dd/yy h:mm a', pivot=True)
    historical_options.configure_columns(["MakerAmt", "MakerAmtETH", "TakerAmt", "TakerAmtETH",
                                          "UnfilledTakerAmt", "UnfilledTakerETH", ],
                                         type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                                         precision=6)
    historical_options.configure_columns(["MakerAmtUSD", "TakerAmtUSD", "UnfilledTakerUSD", "FillPct"],
                                         type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                                         precision=2)
    historical_options.configure_side_bar()
    historical_options.configure_selection("single")
    historical_options.configure_column("Expiry", sort='desc')

    jsFormatting = JsCode("""
            function(params) {
                if (params.data.FillPct >= 0.98) {
                    return {
                        'color': 'white',
                        'backgroundColor': 'green'
                    };
                } else if (params.data.FillPct > 0) {
                    return {
                        'backgroundColor': 'lightgreen'
                    };               
                }
            };
            """)
    historical_options.configure_grid_options(getRowStyle=jsFormatting)

    historical_grid = AgGrid(
        historical_data,
        enable_enterprise_modules=True,
        gridOptions=historical_options.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True)
    return historical_grid


@st.experimental_memo(ttl=5 * 60)
def order_fetch():
    token_data = token_fetch()

    orders_json = requests.get("https://hidingbook.keeperdao.com/api/v1/orders?open=True").json()
    order_data = pd.json_normalize(orders_json["orders"])

    joined_data0 = pd.merge(order_data, token_data,
                            left_on="order.makerToken",
                            right_on="address")
    joined_data = pd.merge(joined_data0, token_data,
                           left_on="order.takerToken",
                           right_on="address",
                           suffixes=("_maker", "_taker"))
    joined_data["order.makerAmount"] = joined_data["order.makerAmount"] / (10 ** joined_data["decimals_maker"])
    joined_data["order.takerAmount"] = joined_data["order.takerAmount"] / (10 ** joined_data["decimals_taker"])
    joined_data["metaData.filledAmount_takerToken"] = \
        joined_data["metaData.filledAmount_takerToken"] / (10 ** joined_data["decimals_taker"])
    joined_data["metaData.remainingFillableAmount_takerToken"] = \
        joined_data["metaData.remainingFillableAmount_takerToken"] / (10 ** joined_data["decimals_taker"])

    return joined_data


# @st.experimental_memo(ttl=5 * 60)
def order_table():
    known_addresses = known_address_fetch()
    raw_order_data = order_fetch()
    order_data = pd.DataFrame(raw_order_data["order.maker"]).rename(columns={"order.maker": "Address"})
    order_data["Name"] = order_data["Address"].map(known_addresses["Name"])
    order_data["Name"][pd.isna(order_data["Name"])] = "Unknown"
    order_data["OrderType"] = order_data["Address"].map(known_addresses["Type"])
    order_data["OrderHash"] = raw_order_data["metaData.orderHash"]
    order_data["OrderSalt"] = raw_order_data["order.salt"]
    order_data["Created"] = pd.to_datetime(raw_order_data["metaData.creation"], unit='s')
    order_data["Expiry"] = pd.to_datetime(raw_order_data["order.expiry"], unit='s')
    order_data["MakerAmt"] = raw_order_data["order.makerAmount"]
    order_data["MakerToken"] = raw_order_data["name_maker"]
    order_data["MakerAmtUSD"] = raw_order_data["order.makerAmount"] * raw_order_data["latest_price.usd_price_maker"]
    order_data["MakerAmtETH"] = raw_order_data["order.makerAmount"] * raw_order_data["latest_price.eth_price_maker"]
    order_data["TakerAmt"] = raw_order_data["order.takerAmount"]
    order_data["TakerToken"] = raw_order_data["name_taker"]
    order_data["TakerAmtUSD"] = raw_order_data["order.takerAmount"] * raw_order_data["latest_price.usd_price_taker"]
    order_data["TakerAmtETH"] = raw_order_data["order.takerAmount"] * raw_order_data["latest_price.eth_price_taker"]
    order_data["UnfilledTakerAmt"] = raw_order_data["metaData.remainingFillableAmount_takerToken"]
    order_data["UnfilledTakerUSD"] = order_data["UnfilledTakerAmt"] * raw_order_data["latest_price.usd_price_taker"]
    order_data["UnfilledTakerETH"] = order_data["UnfilledTakerAmt"] * raw_order_data["latest_price.eth_price_taker"]
    order_data["FillPct"] = raw_order_data["metaData.filledAmount_takerToken"] / raw_order_data["order.takerAmount"]
    order_data["DiffUnfilledUSD"] = (order_data["MakerAmtUSD"] - order_data["TakerAmtUSD"]) * (
            1 - order_data["FillPct"])
    order_data["DiffUnfilledETH"] = (order_data["MakerAmtETH"] - order_data["TakerAmtETH"]) * (
            1 - order_data["FillPct"])
    order_data["DiffPct"] = order_data["MakerAmtUSD"] / order_data["TakerAmtUSD"] - 1

    order_data["OrderType"][(order_data["OrderType"] != "Market Maker") & (
            (order_data["Expiry"] - order_data["Created"]).dt.total_seconds() < 180)] = "AutoFill"
    order_data["OrderType"][(order_data["OrderType"] != "Market Maker") & (
            (order_data["Expiry"] - order_data["Created"]).dt.total_seconds() >= 180)] = "Limit Order"

    order_options = GridOptionsBuilder.from_dataframe(
        order_data,
        enableRowGroup=True,
        enableValue=True,
        enablePivot=True)
    order_options.configure_columns(["Created", "Expiry"], type=["dateColumnFilter", "customDateTimeFormat"],
                                    custom_format_string='MM/dd/yy h:mm a', pivot=True)
    order_options.configure_columns(["MakerAmt", "MakerAmtETH", "TakerAmt", "TakerAmtETH",
                                     "UnfilledTakerAmt", "UnfilledTakerETH", "DiffUnfilledETH", "DiffPct"],
                                    type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                                    precision=6)
    order_options.configure_columns(["MakerAmtUSD", "TakerAmtUSD", "UnfilledTakerUSD", "DiffUnfilledUSD",
                                     "FillPct"],
                                    type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                                    precision=2)
    order_options.configure_side_bar()
    order_options.configure_selection("single")
    order_options.configure_column("Created", sort='desc')

    jsFormatting = JsCode("""
            function(params) {
                if (params.data.FillPct >= 0.98) {
                    return {
                        'color': 'white',
                        'backgroundColor': 'green'
                    };
                } else if (params.data.FillPct > 0) {
                    return {
                        'backgroundColor': 'lightgreen'
                    };               
                }
            };
            """)
    order_options.configure_grid_options(getRowStyle=jsFormatting)

    order_grid = AgGrid(
        order_data,
        enable_enterprise_modules=True,
        gridOptions=order_options.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True)
    return order_grid, order_data


@st.experimental_memo(ttl=1 * 60)
def fills_fetch(order_hash):
    token_data = token_fetch()

    fills_json = requests.get("https://api.rook.fi/api/v1/trade/orderHistory?orderHashes=" + order_hash).json()
    fills_data = pd.json_normalize(fills_json["items"], record_path=["orderFills"])
    if len(fills_data) > 0:
        joined_data0 = pd.merge(fills_data, token_data,
                                left_on="makerToken",
                                right_on="address")
        joined_data = pd.merge(joined_data0, token_data,
                               left_on="takerToken",
                               right_on="address",
                               suffixes=("_maker", "_taker"))
        joined_data["makerTokenFilledAmount"] = joined_data["makerTokenFilledAmount"] / (
                10 ** joined_data["decimals_maker"])
        joined_data["takerTokenFilledAmount"] = joined_data["takerTokenFilledAmount"] / (
                10 ** joined_data["decimals_taker"])
    else:
        joined_data = fills_data

    return joined_data


# @st.experimental_memo(ttl=1 * 60)
def fills_table(order_hash):
    raw_fills_data = fills_fetch(order_hash)

    if len(raw_fills_data) > 0:
        fills_data = pd.DataFrame(raw_fills_data["txHash"])
        fills_data["Taker"] = raw_fills_data["taker"]
        fills_data["Timestamp"] = pd.to_datetime(raw_fills_data["timestamp"], unit='s')
        fills_data["BlockNum"] = raw_fills_data["blockNumber"]
        fills_data["MakerAmtFilled"] = raw_fills_data["makerTokenFilledAmount"]
        fills_data["MakerToken"] = raw_fills_data["name_maker"]
        fills_data["MakerAmtFilledUSD"] = raw_fills_data["makerTokenFilledAmount"] * raw_fills_data[
            "latest_price.usd_price_maker"]
        fills_data["TakerAmtFilled"] = raw_fills_data["takerTokenFilledAmount"]
        fills_data["TakerToken"] = raw_fills_data["name_taker"]
        fills_data["TakerAmtFilledUSD"] = raw_fills_data["takerTokenFilledAmount"] * raw_fills_data[
            "latest_price.usd_price_taker"]
        fills_data["GasUSD"] = raw_fills_data["gasUsed"] * raw_fills_data["gasPrice"] * raw_fills_data[
            "ethPrice"] * 10 ** -9

        fills_options = GridOptionsBuilder.from_dataframe(
            fills_data,
            enableRowGroup=True,
            enableValue=True,
            enablePivot=True)
        fills_options.configure_column("Timestamp", type=["dateColumnFilter", "customDateTimeFormat"],
                                       custom_format_string='MM/dd/yy h:mm a', pivot=True)
        fills_options.configure_columns(["MakerAmtFilled", "TakerAmtFilled"],
                                        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                                        precision=6)
        fills_options.configure_columns(["MakerAmtFilledUSD", "TakerAmtFilledUSD", "GasUSD"],
                                        type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                                        precision=2)
        fills_options.configure_side_bar()
        fills_options.configure_selection("single")
        fills_options.configure_column("Timestamp", sort='asc')

        fills_grid = AgGrid(
            fills_data,
            enable_enterprise_modules=True,
            gridOptions=fills_options.build(),
            update_mode=GridUpdateMode.MODEL_CHANGED)
    else:
        fills_grid = list()
        fills_data = list()
    return fills_grid, fills_data


@st.experimental_memo(ttl=1 * 60)
def auctions_fetch(order_hash):
    auctions_json = requests.get("https://api.rook.fi/api/v1/coordinator/auctions?orderHashes=" + order_hash).json()
    auctions_data = pd.json_normalize(auctions_json, record_path=["bidList"],
                                      meta=["auctionCreationBlockNumber",
                                            "auctionSettlementBlockNumber",
                                            "auctionDeadlineBlockNumber"])

    return auctions_data


# @st.experimental_memo(ttl=1 * 60)
def auctions_table(order_hash):
    raw_auctions_data = auctions_fetch(order_hash)
    if len(raw_auctions_data) > 0:
        auctions_data = pd.DataFrame(raw_auctions_data["keeperIdentityAddress"]).rename(
            columns={"keeperIdentityAddress": "Keeper"})
        auctions_data["CreationBlock"] = raw_auctions_data["auctionCreationBlockNumber"]
        auctions_data["SettlementBlock"] = raw_auctions_data["auctionSettlementBlockNumber"]
        auctions_data["DeadlineBlock"] = raw_auctions_data["auctionDeadlineBlockNumber"]
        auctions_data["RookBidAmt"] = raw_auctions_data["rook_etherUnits"]
        auctions_data["ScoreBid"] = raw_auctions_data["score_bid"]
        auctions_data["ScoreRandom"] = raw_auctions_data["score_random"]
        auctions_data["ScoreFillAmt"] = raw_auctions_data["score_targetFillAmount"]
        auctions_data["ScoreReputation"] = raw_auctions_data["score_reputation"]
        auctions_data["ScoreStake"] = raw_auctions_data["score_stake"]
        auctions_data["Score"] = raw_auctions_data["score"]
        auctions_data["OutcomeValue"] = raw_auctions_data["outcome.outcomeValue"]
        auctions_data["OutcomeReceipt"] = raw_auctions_data["outcome.outcomeReceipt"]
        auctions_data["OutcomeTxHash"] = raw_auctions_data["outcome.txHash"]
        auctions_data["BatchCnt"] = raw_auctions_data["outcome.batchCount"]
        auctions_data["AuctionID"] = raw_auctions_data["auctionId"]
        auctions_data["BidID"] = raw_auctions_data["bidId"]

        auctions_options = GridOptionsBuilder.from_dataframe(
            auctions_data,
            enableRowGroup=True,
            enableValue=True,
            enablePivot=True)
        auctions_options.configure_columns(["BidAmt", "ScoreBid", "ScoreRandom", "ScoreFillAmt",
                                            "ScoreReputation", "ScoreStake", "Score"],
                                           type=["numericColumn", "numberColumnFilter", "customNumericFormat"],
                                           precision=4)
        auctions_options.configure_side_bar()
        auctions_options.configure_selection("single")
        auctions_options.configure_column("CreationBlock", sort='asc')

        jsFormatting = JsCode("""
                function(params) {
                    if (params.data.Outcome == "Filled outside valid range") {
                        return {
                            'color': 'white',
                            'backgroundColor': 'red'
                        };
                    } else if (params.data.BatchCnt > 0) {
                        return {
                            'color': 'white',
                            'backgroundColor': 'green'
                        };
                    }
                };
                """)
        auctions_options.configure_grid_options(getRowStyle=jsFormatting)

        auctions_grid = AgGrid(
            auctions_data,
            enable_enterprise_modules=True,
            gridOptions=auctions_options.build(),
            update_mode=GridUpdateMode.MODEL_CHANGED,
            allow_unsafe_jscode=True)
    else:
        auctions_grid = list()
        auctions_data = list()

    return auctions_grid, auctions_data
