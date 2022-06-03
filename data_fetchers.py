import streamlit as st
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


@st.cache
def token_fetch():
    token_json = requests.get("https://api.rook.fi/api/v1/trade/tokens").json()
    token_data = pd.json_normalize(token_json)
    token_data = token_data.drop(columns=["coingecko_id", "active", "latest_price.timestamp",
                                          "trade_info.makerTokenTradeCount", "trade_info.takerTokenTradeCount",
                                          "trade_info.mostRecentTradeTimestamp"])

    return token_data


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


@st.cache
def historical_fetch(address):
    token_data = token_fetch()

    historical_json = requests.get(
        "https://api.rook.fi/api/v1/trade/orderHistory?makerAddresses=" +
        address + "&limit=100&offset=0").json()
    historical_data = pd.json_normalize(historical_json["items"])

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

    historical_grid = AgGrid(
        historical_data,
        enable_enterprise_modules=True,
        gridOptions=historical_options.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED)
    return historical_grid


@st.cache
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


def order_table():
    raw_order_data = order_fetch()
    order_data = pd.DataFrame(raw_order_data["order.maker"]).rename(columns={"order.maker": "Address"})
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

    order_grid = AgGrid(
        order_data,
        enable_enterprise_modules=True,
        gridOptions=order_options.build(),
        update_mode=GridUpdateMode.MODEL_CHANGED)
    return order_grid


@st.cache
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
        fills_grid = AgGrid(
            fills_data,
            enable_enterprise_modules=True,
            gridOptions=fills_options.build(),
            update_mode=GridUpdateMode.MODEL_CHANGED)
    else:
        fills_grid = []
    return fills_grid


@st.cache
def auctions_fetch(order_hash):
    auctions_json = requests.get("https://api.rook.fi/api/v1/coordinator/auctions?orderHashes=" + order_hash).json()
    auctions_data = pd.json_normalize(auctions_json, record_path=["bidList"],
                                      meta=["auctionCreationBlockNumber",
                                            "auctionSettlementBlockNumber",
                                            "auctionDeadlineBlockNumber"])

    return auctions_data


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

        auctions_grid = AgGrid(
            auctions_data,
            enable_enterprise_modules=True,
            gridOptions=auctions_options.build(),
            update_mode=GridUpdateMode.MODEL_CHANGED)
    else:
        auctions_grid = []
    return auctions_grid
