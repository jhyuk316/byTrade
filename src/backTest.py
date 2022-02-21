from datetime import datetime
import heapq
import threading
import time
from typing import Dict

import market
import strategy
from pybit import HTTP
import pandas as pd
import matplotlib.pyplot as plt


class Account:
    def __init__(self, qty) -> None:
        self.usdt = 3000
        self.shortPrice = 0  # 숏 평단가.
        self.numShortCoin = 0  # 숏 갯수.
        self.longPrice = 0
        self.numLongCoin = 0
        self.qty = qty

    def estimatedTotal(self, price: float) -> float:
        shortBenefit = self.numShortCoin * self.qty * (2 * self.shortPrice - price)
        longBenefit = self.numLongCoin * self.qty * price
        return self.usdt + shortBenefit + longBenefit

    def openShort(self, price: float) -> str:
        if price * self.qty < self.usdt:
            self.usdt -= self.qty * price
            self.shortPrice = (self.shortPrice * self.numShortCoin + price) / (
                self.numShortCoin + 1
            )
            self.numShortCoin += 1
            return "openShort"
        else:
            print("Fail openShort Account have not enough usdt")
            return "Fail openShort"

    def closeShort(self, price: float) -> str:
        if self.numShortCoin > 0:
            self.usdt += self.qty * (2 * self.shortPrice - price)
            if self.numShortCoin == 1:
                self.shortPrice = 0
            else:
                self.shortPrice = (self.shortPrice * self.numShortCoin - price) / (
                    self.numShortCoin - 1
                )
            self.numShortCoin -= 1
            return "closeShort"
        else:
            print("Fail closeShort Account have not short")
            return "Fail closeShort"

    def openLong(self, price: float) -> str:
        if price * self.qty < self.usdt:
            self.usdt -= self.qty * price
            self.longPrice = (self.longPrice * self.numLongCoin + price) / (
                self.numLongCoin + 1
            )
            self.numLongCoin += 1
            return "openLong"
        else:
            print("Fail openLong Account have not enough usdt")
            return "Fail openLong"

    def closeLong(self, price: float) -> str:
        if self.numLongCoin > 0:
            self.usdt += self.qty * price
            if self.numLongCoin == 1:
                self.longPrice = 0
            else:
                self.longPrice = (self.longPrice * self.numLongCoin - price) / (
                    self.numLongCoin - 1
                )
            self.numLongCoin -= 1
            return "closeLong"
        else:
            print("Fail closeLong Account have not long")
            return "Fail closeLong"

    def allCloseLong(self, price: float) -> str:
        while self.numLongCoin > 0:
            self.closeLong(price)
        return "AllCloseLong"

    def allCloseShort(self, price: float) -> str:
        while self.numShortCoin > 0:
            self.closeShort(price)
        return "AllCloseShort"

    def toDict(self) -> Dict:
        return {
            "USDT": self.usdt,
            "ShortCoin": self.shortPrice,
            "Number of ShortCoin": self.numShortCoin,
            "LongCoin": self.longPrice,
            "Number of LongCoin": self.numLongCoin,
        }

    def toDataFrame(self) -> pd.DataFrame:
        return pd.DataFrame(self.toDict(), index=[0])

    def __str__(self) -> str:
        return str(self.toDict())


class AccountBook:
    def __init__(self, account: Account, startDate: datetime) -> None:
        self.account = account
        tradeData = {
            "TradeTime": startDate,
            "Side": None,
            "Price": None,
            "USDT": self.account.usdt,
            "EstiUSDT": self.account.usdt,
            "EarningRate %": None,
            "TotalEarningRate %": None,
        }
        self.book = pd.DataFrame(tradeData, index=[0])

    def write(self, tradeTime: int, side: str, price: float) -> None:
        EarningRate = (
            self.account.estimatedTotal(price) / self.book["EstiUSDT"].iloc[-1] - 1
        )
        TotalEarningRate = (
            self.account.estimatedTotal(price) / self.book["EstiUSDT"].iloc[0] - 1
        )

        tradeData = {
            "TradeTime": str(datetime.fromtimestamp(tradeTime)),
            "Side": side,
            "Price": price,
            "USDT": self.account.usdt,
            "EstiUSDT": self.account.estimatedTotal(price),
            "EarningRate %": f"{EarningRate * 100:.2f}",
            "TotalEarningRate %": f"{TotalEarningRate * 100:.2f}",
        }
        # print(tradeData)
        # self.book = self.book.append(tradeData, ignore_index=True)
        tempDF = pd.DataFrame([tradeData])
        self.book = pd.concat([self.book, tempDF], ignore_index=True)

    def toDataFrame(self) -> pd.DataFrame:
        return self.book


class BackTest(threading.Thread):
    def __init__(
        self,
        marketType: market.Type,
        symbol: str,
        startDate: datetime,
        endDate: datetime,
        quantity: float,
        tickInterval: int = 1,
        shortMA: int = 18,
        longMA: int = 60,
        BBFactor: int = 2,
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
        self.qty = quantity

        self.account = Account(self.qty)
        self.accountBook = AccountBook(self.account, startDate)

        print(self.accountBook)
        print(self.account)

    def getData(self, startTime: int, limit: int = 200) -> pd.DataFrame:
        data = self.readSession.query_kline(
            symbol=self.symbol,
            interval=self.tickInterval,
            limit=limit,  # MAX 200
            from_time=int(startTime),
        )
        resultData = pd.DataFrame(data["result"])
        time.sleep(0.1)  # API 과다 호출 방지
        return resultData

    def run(self):

        # 시작 지점 -60 데이터 프리 로드
        pd.set_option("display.max_rows", 100)
        lastTime = int(
            self.startDate.timestamp()
            - (self.longMovingAverageTerm) * 60 * self.tickInterval
        )

        data = self.getData(lastTime, self.longMovingAverageTerm)
        lastTime = int(data["open_time"].iloc[-1]) + 1

        while lastTime < self.endDate.timestamp():
            print("Load Data from Time : ", datetime.fromtimestamp(lastTime))
            resultdata: pd.DataFrame = self.getData(lastTime)
            lastTime: int = int(resultdata["open_time"].iloc[-1]) + 1

            data: pd.DataFrame = pd.concat([data, resultdata], ignore_index=True)

            # dateString = datetime.fromtimestamp(lastTime).strftime("%y.%m.%d %H%M%S")
            # data.to_csv(f"result/data{dateString}.csv")

        closeData: pd.DataFrame = data["close"]
        shortMA = closeData.rolling(window=self.shortMovingAverageTerm).mean()
        longMA = closeData.rolling(window=self.longMovingAverageTerm).mean()
        longMAStd = closeData.rolling(window=self.longMovingAverageTerm).std()

        for i in range(self.longMovingAverageTerm, len(closeData)):
            tradeTime: int = data["open_time"].iloc[i]

            coinData = strategy.CoinData(
                float(shortMA.iloc[i]),
                float(longMA.iloc[i]),
                float(longMAStd.iloc[i]),
                float(closeData.iloc[i]),
            )

            # 전략 수행
            self.strategy.decide(coinData)
            side = ""
            if self.strategy.openShort:
                side = self.account.openShort(coinData.close)
                if not self.strategy.isInBox:
                    side += "*"
                self.accountBook.write(tradeTime, side, coinData.close)

            if self.strategy.closeShort:
                side = self.account.closeShort(coinData.close)
                if not self.strategy.isInBox:
                    side += "*"
                self.accountBook.write(tradeTime, side, coinData.close)

            if self.strategy.openLong:
                side = self.account.openLong(coinData.close)
                if not self.strategy.isInBox:
                    side += "*"
                self.accountBook.write(tradeTime, side, coinData.close)

            if self.strategy.closeLong:
                side = self.account.closeLong(coinData.close)
                if not self.strategy.isInBox:
                    side += "*"
                self.accountBook.write(tradeTime, side, coinData.close)

            if self.strategy.allCloseLong:
                side = self.account.allCloseLong(coinData.close)
                if not self.strategy.isInBox:
                    side += "*"
                self.accountBook.write(tradeTime, side, coinData.close)

            if self.strategy.allCloseShort:
                side = self.account.allCloseShort(coinData.close)
                if not self.strategy.isInBox:
                    side += "*"
                self.accountBook.write(tradeTime, side, coinData.close)

        accountBook = self.accountBook.toDataFrame()
        account = self.account.toDataFrame()

        print(accountBook)
        print(account)

        try:
            accountBook.to_csv(f"result/{self.symbol} accountBook.csv")
            account.to_csv(f"result/{self.symbol} account.csv")
        except:
            accountBook.to_csv(f"result/{self.symbol} accountBook.temp")
            account.to_csv(f"result/{self.symbol} account.temp")

        data.plot(x="open_time", y="close")
        plt.show()
