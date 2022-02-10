from datetime import datetime
import threading
import time

import pandas as pd
from pybit import HTTP

import apiKey as Key
import market
import strategy


class Trade(threading.Thread):
    def __init__(
        self,
        marketType: market.Type,
        # tradeType: market.TradeType,
        symbol: str,
        shortMA: int = 18,
        longMA: int = 60,
        BBFactor: int = 2,
        tickInterval: int = 1,
    ) -> None:
        threading.Thread.__init__(self)
        mURL = market.URL(marketType, market.TradeType.MAIN)
        self.urlRestBybit = mURL.urlRestBybit
        self.urlWebSocketPublic = mURL.urlWebSocketPublic
        self.urlWebSocketPrivate = mURL.urlWebSocketPrivate

        self.apiKey = Key.apiKey
        self.apiSecret = Key.apiSecret
        self.symbol = symbol
        # tick_interval 1 3 5 15 30 60 120 240 360 720 "D" "M" "W"
        self.tickInterval = tickInterval

        self.strategy = strategy.Strategy(BBFactor)

        self.shortMovingAverageTerm = shortMA
        self.longMovingAverageTerm = longMA

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
            readSession = HTTP(self.urlRestBybit)
            data = readSession.query_kline(
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
            upBB = longMA + self.bollingerBandsFactor * longMAStd
            downBB = longMA - self.bollingerBandsFactor * longMAStd

            # 구매 판매가 설정
            orderBookData = readSession.orderbook(symbol=self.symbol)
            orderBookData = pd.DataFrame(orderBookData["result"])
            buyPrice = orderBookData["price"].iloc[25]  # 25번 행 buy 가격
            sellPrice = orderBookData["price"].iloc[24]  # 24번 행 sell 가격
            print("Buy Sell Price ", buyPrice, sellPrice)

            coinData = strategy.CoinData(
                shortMA.iloc[-1],
                longMA.iloc[-1],
                longMAStd.iloc[-1],
                closeData.iloc[-1],
            )

            # 구입 판매 결정
            accountSession = HTTP(self.urlRestBybit, self.apiKey, self.apiSecret)
            self.strategy.decide(coinData)

            # 전략 수행
            self.strategy.decide(coinData)
            side = ""
            if self.strategy.openShort:
                print("Limit에 open Short {self.symbol} {buyPrice}")
                openShortResult = accountSession.place_active_order(
                    symbol=self.symbol,
                    side="Buy",
                    order_type="Limit",
                    qty=0.01,
                    price=buyPrice,
                    time_in_force=True,
                    reduce_only=False,
                )
                print(openShortResult)

            if self.strategy.closeShort:
                # TODO closeShort
                print("Limit에 close Short {self.symbol} {buyPrice}")

            if self.strategy.openLong:
                # TODO openLong
                print("Limit에 open long {self.symbol} {buyPrice}")

            if self.strategy.closeLong:
                # TODO closeLong
                print("Limit에 open Short {self.symbol} {buyPrice}")

            if self.strategy.allCloseLong:
                # TODO allCloseLong
                print("Limit에 allCloseLong {self.symbol} {buyPrice}")

            if self.strategy.allCloseShort:
                # TODO allCloseShort
                print("Limit에 allCloseShort {self.symbol} {buyPrice}")

            term = 60 * self.tickInterval + 1 - diffTime
            time.sleep(term if term > 0 else 0)

