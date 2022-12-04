from datetime import datetime
import threading
import time

import pandas as pd
from pybit import usdt_perpetual

import apiKey as Key
import market
import strategy


class Trade(threading.Thread):
    def __init__(
            self,
            marketType: market.Type = market.Type.USDTPerpetual,
            tradeType: market.TradeType = market.TradeType.TEST,
            symbol: str = "XRPUSDT",
            shortMA: int = 18,
            longMA: int = 60,
            BBFactor: int = 2,
            tickInterval: int = 1,
            quantity: float = 0.01,
    ) -> None:
        threading.Thread.__init__(self)
        mURL = market.URL(marketType, tradeType)
        self.urlRestBybit = mURL.urlRestBybit
        self.urlWebSocketPublic = mURL.urlWebSocketPublic
        self.urlWebSocketPrivate = mURL.urlWebSocketPrivate

        self.apiKey = Key.apiKey
        self.apiSecret = Key.apiSecret
        self.symbol = symbol
        # tick_interval 1 3 5 15 30 60 120 240 360 720 "D" "M" "W"
        self.tickInterval = tickInterval
        self.qty = quantity

        self.strategy = strategy.Strategy(BBFactor)

        self.shortMovingAverageTerm = shortMA
        self.longMovingAverageTerm = longMA

        self.session_unauth = usdt_perpetual.HTTP(
            endpoint=mURL.urlRestBybit
        )

        self.session_auth = usdt_perpetual.HTTP(
            endpoint=mURL.urlRestBybit,
            api_key=Key.apiKey,
            api_secret=Key.apiSecret
        )
        print("marketURL ", mURL.urlRestBybit)
        print("symbol", symbol)

    def setMATerm(self, short: int, long: int) -> None:
        if short >= long:
            return

        self.shortMovingAverageTerm = short
        self.longMovingAverageTerm = long

    def printConfig(self):
        print(self.urlRestBybit)
        print(self.urlWebSocketPublic)
        print(self.urlWebSocketPrivate)

        print(self.symbol)
        print(self.shortMovingAverageTerm)
        print(self.longMovingAverageTerm)
        print(self.bollingerBandsFactor)

    def run(self):
        print("start trading ", self.symbol)

        while True:
            # TODO - 정보 읽기 분리
            # 시장 정보 가져오기
            data = self.session_unauth.query_kline(
                symbol=self.symbol,
                interval=self.tickInterval,
                limit=200,  # MAX 200
                from_time=int(
                    time.time() - self.longMovingAverageTerm * 60 * self.tickInterval
                ),
            )
            dataDF = pd.DataFrame(data["result"])
            diffTime = int(time.time()) - dataDF["open_time"].iloc[-1]
            print(f"현재 시각 {datetime.fromtimestamp(time.time())} 분봉 시간차 {diffTime}")

            closeData = dataDF["close"]

            # print(closeData)

            shortMA = closeData.rolling(window=self.shortMovingAverageTerm).mean()
            longMA = closeData.rolling(window=self.longMovingAverageTerm).mean()

            longMAStd = closeData.rolling(window=self.longMovingAverageTerm).std()

            # 구매 판매가 설정
            orderBookData = self.session_unauth.orderbook(symbol=self.symbol)
            orderBookData = pd.DataFrame(orderBookData["result"])
            buyPrice = orderBookData["price"].iloc[25]  # 25번 행 buy 가격
            sellPrice = orderBookData["price"].iloc[24]  # 24번 행 sell 가격
            print("Buy Sell Price ", buyPrice, sellPrice)

            coinData = strategy.CoinData(
                shortMA=shortMA.iloc[-1],
                longMA=longMA.iloc[-1],
                longMAStd=longMAStd.iloc[-1],
                close=closeData.iloc[-1],
            )

            # 주요 개념
            # Time In Force
            # https://www.bybit.com/en-US/help-center/bybitHC_Article?language=en_US&id=000001044
            # reduce_only
            # https://ascendex.com/ko/support/articles/49610-what-is-a-reduce-only-order
            # close_on_trigger
            # ??

            # 전략 수행
            self.strategy.decide(coinData)
            side = ""

            # 체결되지 않은 거래 모두 취소
            # active_order = self.session_auth.get_active_order(symbol=self.symbol)
            # print(active_order);
            print("cancel_all_active_orders")
            cancel_all_active_orders = self.session_auth.cancel_all_active_orders(symbol=self.symbol)
            print(cancel_all_active_orders)

            if self.strategy.openShort:
                print("Limit에 open Short {self.symbol} {buyPrice}")
                openShortResult = self.session_auth.place_active_order(
                    symbol=self.symbol,
                    side="Sell",
                    order_type="Limit",
                    qty=self.qty,
                    price=buyPrice,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False
                )
                print(openShortResult)

            if self.strategy.closeShort:
                # TODO closeShort
                print("Limit에 close Short {self.symbol} {buyPrice}")
                closeShort = self.session_auth.place_active_order(
                    symbol=self.symbol,
                    side="Buy",
                    order_type="Limit",
                    qty=self.qty,
                    price=buyPrice,
                    time_in_force="GoodTillCancel",
                    reduce_only=True,
                    close_on_trigger=False
                )
                print(closeShort)

            if self.strategy.openLong:
                # TODO openLong
                print("Limit에 open long {self.symbol} {buyPrice}")
                closeShort = self.session_auth.place_active_order(
                    symbol=self.symbol,
                    side="Buy",
                    order_type="Limit",
                    qty=self.qty,
                    price=buyPrice,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False
                )
                print(closeShort)

            if self.strategy.closeLong:
                # TODO closeLong
                print("Limit에 close Long {self.symbol} {buyPrice}")
                closeShort = self.session_auth.place_active_order(
                    symbol=self.symbol,
                    side="Sell",
                    order_type="Limit",
                    qty=self.qty,
                    price=buyPrice,
                    time_in_force="GoodTillCancel",
                    reduce_only=True,
                    close_on_trigger=False
                )
                print(closeShort)

            if self.strategy.allCloseLong:
                # TODO allCloseLong
                print("Limit에 allCloseLong {self.symbol} {buyPrice}")

            if self.strategy.allCloseShort:
                # TODO allCloseShort
                print("Limit에 allCloseShort {self.symbol} {buyPrice}")

            term = 60 * self.tickInterval + 1 - diffTime
            time.sleep(term if term > 0 else 0)


if __name__ == "__main__":
    symbol = "XRPUSDT"
    session_unauth = usdt_perpetual.HTTP(
        endpoint="https://api-testnet.bybit.com"
    )
    orderbook = session_unauth.orderbook(symbol=symbol)
    print(orderbook)

    orderBookData = session_unauth.orderbook(symbol=symbol)
    orderBookData = pd.DataFrame(orderBookData["result"])
    print("orderBookData")
    print(orderBookData)
    buyPrice = orderBookData["price"].iloc[26]  # 25번 행 buy 가격
    sellPrice = orderBookData["price"].iloc[23]  # 24번 행 sell 가격
    print("Buy Sell Price ", buyPrice, sellPrice)

    session_auth = usdt_perpetual.HTTP(
        endpoint="https://api.bybit.com",
        api_key=Key.apiKey,
        api_secret=Key.apiSecret
    )

    cancel_all_active_orders = session_auth.cancel_all_active_orders(symbol=symbol)
    print(cancel_all_active_orders)

    print("Limit에 open Short {self.symbol} {buyPrice}")
    place_active_order = session_auth.place_active_order(symbol=symbol, side="Sell", order_type="Limit", qty=1,
                                                         price=buyPrice,
                                                         time_in_force="GoodTillCancel", reduce_only=False,
                                                         close_on_trigger=False)
    print(place_active_order)
