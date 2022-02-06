# 참조 소스코드
# https://limetimeline.tistory.com/433

import pandas as pd
import datetime
import requests
import time
import calendar
from pybit import HTTP
from datetime import datetime, timedelta, timezone

from requests.api import post

import apiKey as Key

apiKey = Key.apiKey
apiSecret = Key.apiSecret

# symbol to be traded
symbol = "MANAUSDT"

query_kilne = "https://api.bybit.com/public/linear/kline?symbol="  # USDT
# query_kilne = 'https://api.bybit.com/v2/public/kline/list?symbol=' # USD
latest_infoSymbol = "https://api.bybit.com/v2/public/tickers?symbol="

# candle in minutes
tick_interval = "1"

# quantity to be traded in USD
qty1 = 3

opt = 0
while True:
    bybitticker = symbol

    now = datetime.utcnow()
    unixtime = calendar.timegm(now.utctimetuple())
    since = unixtime

    start = str(since - 60 * 60 * int(tick_interval))
    url = (
        query_kilne + bybitticker + "&interval=" + tick_interval + "&from=" + str(start)
    )
    data = requests.get(url).json()
    D = pd.DataFrame(data["result"])

    marketprice = latest_infoSymbol + symbol
    res = requests.get(marketprice)
    data = res.json()
    lastprice = float(data["result"][0]["last_price"])

    price = lastprice
    df = D["close"]

    ma9 = df.rolling(window=9).mean()
    ma26 = df.rolling(window=26).mean()

    test1 = ma9.iloc[-2] - ma26.iloc[-2]
    test2 = ma9.iloc[-1] - ma26.iloc[-1]

    session = HTTP(
        endpoint="https://api.bybit.com/", api_key=apiKey, api_secret=apiSecret
    )

    positionsize = session.my_position(symbol=symbol)["result"][0]["size"]
    if session.my_position(symbol=symbol)["result"][0]["side"] == "Sell":
        positionsize = positionsize * -1

        lastprice = float(
            session.latest_information_for_symbol(symbol=symbol)["result"][0][
                "last_price"
            ]
        )
    call = "None"

    # try:
    #     if test1 > 0 and test2 < 0:
    #         if positionsize > 0:
    #             print("skip")
    #             time.sleep(2)
    #             continue
    #         call = "Dead Cross"
    #         qty = qty1
    #         if positionsize < 0:
    #             qty = qty1 + abs(positionsize)

    #         if opt == 0:
    #             opt = 1

    #             print(
    #                 session.place_active_order(
    #                     symbol=bybitticker,
    #                     side="Buy",
    #                     order_type="Market",
    #                     qty=qty1,
    #                     time_in_force="GoodTillCancel",
    #                     reduce_only=False,
    #                     close_on_trigger=False,
    #                 )
    #             )

    #             print(
    #                 session.place_active_order(
    #                     symbol=bybitticker,
    #                     side="Buy",
    #                     order_type="Market",
    #                     qty=qty1,
    #                     time_in_force="GoodTillCancel",
    #                     reduce_only=True,
    #                     close_on_trigger=False,
    #                 )
    #             )

    #     if test1 < 0 and test2 > 0:
    #         if positionsize < 0:
    #             print("skip")
    #             time.sleep(2)
    #             continue
    #         call = "Golden Cross"
    #         qty = qty1

    #         if positionsize > 0:
    #             qty = qty1 + abs(positionsize)
    #         if opt == 1:
    #             opt = 0
    #             print(
    #                 session.place_active_order(
    #                     symbol=bybitticker,
    #                     side="Sell",
    #                     order_type="Market",
    #                     qty=qty1,
    #                     time_in_force="GoodTillCancel",
    #                     reduce_only=True,
    #                     close_on_trigger=False,
    #                 )
    #             )

    #             print(
    #                 session.place_active_order(
    #                     symbol=bybitticker,
    #                     side="Sell",
    #                     order_type="Market",
    #                     qty=qty1,
    #                     time_in_force="GoodTillCancel",
    #                     reduce_only=False,
    #                     close_on_trigger=False,
    #                 )
    #             )
    # except:
    #     pass

    print("Name: ", bybitticker)
    print("Date: ", now)
    print("price: ", lastprice)
    print("MA 9: ", round(ma9.iloc[-1], 2))
    print("MA 26: ", round(ma26.iloc[-1], 2))
    print("Golden Cross/Dead Cross: ", call)
    print("opt: ", opt)
    print("")

    time.sleep(5)
