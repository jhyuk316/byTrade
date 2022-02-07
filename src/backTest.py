from datetime import datetime
import heapq
import threading
import time
from unittest import result

import market
import strategy
from pybit import HTTP
import pandas as pd


class Account:
    def __init__(self, qty) -> None:
        self.usdt = 3000
        self.coinList = []
        self.qty = qty

    def averageCoin(self) -> float:
        if not self.coinList:
            return 0

        return sum(self.coinList) / len(self.coinList)

    def amountCoin(self) -> int:
        return len(self.coinList)

    def estimatedTotalAcount(self, price: float) -> float:
        return self.usdt + self.amountCoin() * self.qty * (
            price + 2 * (self.averageCoin() - price)
        )

    def __str__(self) -> str:
        return f"USDT : {self.usdt}, Coin : {self.coinList}, averageCoin : {self.averageCoin()}, amount : {self.amountCoin()}"


class BackTest(threading.Thread):
    def __init__(
        self,
        marketType: market.Type,
        symbol: str,
        startDate: datetime,
        endDate: datetime,
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

        self.symbol = symbol
        # tick_interval 1 3 5 15 30 60 120 240 360 720 "D" "M" "W"
        self.tickInterval = tickInterval

        self.strategy = strategy.Strategy(BBFactor)

        self.shortMovingAverageTerm = shortMA
        self.longMovingAverageTerm = longMA

        self.startDate = startDate
        self.endDate = endDate

        self.readSession = HTTP(self.urlRestBybit)
        self.qty = 100

        self.account = Account(self.qty)

        # accountBook 초기화
        tradeData = {
            "TradeTime": self.startDate,
            "Side": None,
            "Price": None,
            "USDT": self.account.usdt,
            "EstiUSDT": self.account.usdt,
            "EarningRate": None,
            "TotalEarningRate": None,
        }
        self.accountBook = pd.DataFrame(tradeData, index=[0])
        print(self.accountBook)

    def getData(self, startTime: int, limit: int = 200) -> pd.DataFrame:
        data = self.readSession.query_kline(
            symbol=self.symbol,
            interval=self.tickInterval,
            limit=limit,  # MAX 200
            from_time=int(startTime),
        )

        resultData = pd.DataFrame(data["result"])
        # resultData.set_index("open_time", inplace=True)
        return resultData

    def run(self):

        # 시작 지점 -60 데이터 프리 로드
        pd.set_option("display.max_rows", 100)
        lastTime = int(
            self.startDate.timestamp()
            - (self.longMovingAverageTerm) * 60 * self.tickInterval
        )

        data = self.getData(lastTime, 60)
        lastTime = int(data["open_time"].iloc[-1]) + 1

        while lastTime < self.endDate.timestamp():
            print("time : ", datetime.fromtimestamp(lastTime))
            resultdata: pd.DataFrame = self.getData(lastTime)
            lastTime = int(data["open_time"].iloc[-1]) + 1
            time.sleep(0.01)  # API 과다 호출 방지

            data = data.iloc[-60:].append(resultdata, ignore_index=True)

            closeData = data["close"]
            shortMA = closeData.rolling(window=self.shortMovingAverageTerm).mean()
            longMA = closeData.rolling(window=self.longMovingAverageTerm).mean()
            longMAStd = closeData.rolling(window=self.longMovingAverageTerm).std()

            i = 60
            while i < len(closeData):
                tradeTime = data["open_time"].iloc[i]

                coinData = strategy.CoinData(
                    float(shortMA.iloc[i]),
                    float(longMA.iloc[i]),
                    float(longMAStd.iloc[i]),
                    float(closeData.iloc[i]),
                )

                decision = self.strategy.decide(coinData)
                side = ""
                if decision == strategy.Decision.openShort:
                    # print(f"Limit에 open Short {self.symbol} {coinData.close}")
                    if self.account.usdt > coinData.close * self.qty:
                        self.account.usdt -= coinData.close * self.qty
                        heapq.heappush(self.account.coinList, coinData.close)
                        self.account.usdt -= coinData.close * self.qty
                        heapq.heappush(self.account.coinList, coinData.close)
                        side = "openShort"
                    else:
                        side = "Fail openShort"
                        print(
                            f"Fail : Limit에 open Short {self.symbol} {coinData.close}"
                        )

                elif decision == strategy.Decision.closeShort:
                    if self.account.coinList:
                        # print(f"Limit에 close Short {self.symbol} {coinData.close}")
                        benefit = heapq.heappop(self.account.coinList) - coinData.close
                        self.account.usdt += (coinData.close + 2 * benefit) * self.qty
                        side = "closeShort"
                    else:
                        side = "Fail closeShort"
                        print(
                            f"Fail : Limit에 close Short {self.symbol} {coinData.close}"
                        )

                elif decision == strategy.Decision.openLong:
                    print(f"Limit에 open Long {self.symbol} {coinData.close}")
                elif decision == strategy.Decision.closeLong:
                    print(f"Limit에 close long {self.symbol} {coinData.close}")

                # 자산 변동 기록
                if decision != strategy.Decision.hold:
                    tradeData = {
                        "TradeTime": str(datetime.fromtimestamp(tradeTime)),
                        "Side": side,
                        "Price": coinData.close,
                        "USDT": self.account.usdt,
                        "EstiUSDT": self.account.estimatedTotalAcount(coinData.close),
                        "EarningRate": self.account.estimatedTotalAcount(coinData.close)
                        / self.accountBook["EstiUSDT"].iloc[-1],
                        "TotalEarningRate": self.account.estimatedTotalAcount(
                            coinData.close
                        )
                        / self.accountBook["EstiUSDT"].iloc[0],
                    }
                    # print(tradeData)
                    self.accountBook = self.accountBook.append(
                        tradeData, ignore_index=True
                    )

                i += 1

        self.accountBook.to_csv("accountBook.csv")
        print(self.accountBook)
        print(self.account)

