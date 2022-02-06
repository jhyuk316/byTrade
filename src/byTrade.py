from datetime import datetime
import threading
import time

import pandas as pd
from pybit import HTTP

import apiKey as Key
import market


class Trade(threading.Thread):
    def __init__(
        self,
        marketType: market.Type,
        tradeType: market.TradeType,
        symbol: str,
        shortMA: int = 18,
        longMA: int = 60,
        BBFactor: int = 2,
        tickInterval: int = 1,
    ) -> None:
        threading.Thread.__init__(self)
        mURL = market.URL(marketType, tradeType)
        self.urlRestBybit = mURL.urlRestBybit
        self.urlWebSocketPublic = mURL.urlWebSocketPublic
        self.urlWebSocketPrivate = mURL.urlWebSocketPrivate

        self.apiKey = Key.apiKey
        self.apiSecret = Key.apiSecret
        self.symbol = symbol
        self.shortMovingAverageTerm = shortMA
        self.longMovingAverageTerm = longMA
        self.bollingerBandsFactor = BBFactor
        # tick_interval 1 3 5 15 30 60 120 240 360 720 "D" "M" "W"
        self.tickInterval = tickInterval
        self.isResistUpBB = False
        self.isResistDownBB = False

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
            # 시장 정보 가져오기
            readSession = HTTP(self.urlRestBybit)
            data = readSession.query_kline(
                symbol=self.symbol,
                interval=self.tickInterval,
                limit=200,  # MAX 200
                from_time=int(
                    time.time()
                    - (self.longMovingAverageTerm + 2) * 60 * self.tickInterval
                ),
            )
            dataDF = pd.DataFrame(data["result"])
            diffTime = int(time.time()) - dataDF["open_time"].iloc[-1]
            print(f"현재 시각 {datetime.fromtimestamp(time.time())} 분봉 시간차 {diffTime}")

            closeData = dataDF["close"]

            # print(closeData)

            shortMA = closeData.rolling(window=self.shortMovingAverageTerm).mean()
            longMA = closeData.rolling(window=self.longMovingAverageTerm).mean()

            # print(longMA)

            longMAStd = closeData.rolling(window=self.longMovingAverageTerm).std()
            upBB = longMA + self.bollingerBandsFactor * longMAStd
            downBB = longMA - self.bollingerBandsFactor * longMAStd

            # 안정장 BB 1%내
            print(
                f"BW {2*self.bollingerBandsFactor*longMAStd.iloc[-1]/longMA.iloc[-1]*100}%"
            )
            if self.bollingerBandsFactor * longMAStd.iloc[-1] < longMA.iloc[-1] * 0.005:
                isInBox = True
            else:
                isInBox = False

            prevClosePrice = float(dataDF["close"].iloc[-2])
            lastClosePrice = float(dataDF["close"].iloc[-1])
            print(f"현재 종가 {lastClosePrice}")

            # 구매 판매가 설정
            orderBookData = readSession.orderbook(symbol=self.symbol)
            orderBookData = pd.DataFrame(orderBookData["result"])
            buyPrice = orderBookData["price"].iloc[25]  # 25번 행 buy 가격
            sellPrice = orderBookData["price"].iloc[24]  # 24번 행 sell 가격
            print("Buy Sell Price ", buyPrice, sellPrice)

            # 구입 판매 결정
            accountSession = HTTP(self.urlRestBybit, self.apiKey, self.apiSecret)

            if isInBox:  # 안정장
                print("안정장")
                # 종가가 upBB를 넘었을때
                if lastClosePrice > upBB.iloc[-1]:
                    self.isResistUpBB = True

                if self.isResistUpBB and lastClosePrice < shortMA.iloc[-1]:
                    # open short position
                    self.isResistUpBB = False
                    print("Limit에 open Short {self.symbol} {buyPrice}")
                    # openShortResult = accountSession.place_active_order(
                    #     symbol=self.symbol,
                    #     side="Buy",
                    #     order_type="Limit",
                    #     qty=0.01,
                    #     price=buyPrice,
                    #     time_in_force=True,
                    #     reduce_only=False,
                    # )

                # 진전 종가가 down를 넘었을때
                if lastClosePrice < downBB.iloc[-1]:
                    self.isResistDownBB = True

                if self.isResistDownBB and lastClosePrice > shortMA.iloc[-1]:
                    # close Short position
                    self.isResistDownBB = False
                    print("Limit에 close Short {self.symbol} {sellPrice}")
                    # closeShortResult = accountSession.place_active_order(
                    #     symbol=self.symbol,
                    #     side="Sell",
                    #     order_type="Limit",
                    #     qty=0.01,
                    #     price=sellPrice,
                    #     time_in_force=True,
                    #     reduce_only=False,
                    # )
            else:  # 변동장
                print("변동장")
                # 포지션 확인 있는가 없는가?
                # 포지션 있음
                if shortMA.iloc[-1] > longMA.iloc[-1]:
                    # 손절
                    print("Limit에 close Short {self.symbol} {sellPrice}")
                    pass

            term = 60 * self.tickInterval + 1 - diffTime
            time.sleep(term if term > 0 else 0)

