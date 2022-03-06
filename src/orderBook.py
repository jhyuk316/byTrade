from datetime import datetime
import time
from pybit import HTTP
import pandas as pd


class OrderBook:
    def __init__(self, symbol) -> None:
        self.readSession = HTTP("http://api.bybit.com")
        self.symbol = symbol

    def print(self):
        orderBookData = self.readSession.orderbook(symbol=self.symbol)
        orderBookData = pd.DataFrame(orderBookData["result"])
        print(orderBookData)


if __name__ == "__main__":
    orderBook = OrderBook("BTCUSDT")

    while True:
        print(datetime.now())
        orderBook.print()
        time.sleep(10)

