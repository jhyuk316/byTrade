from datetime import datetime
from backTest import BackTest
import market
from byTrade import Trade

if __name__ == "__main__":
    print("hello")

    # trade = Trade(market.Type.USDTPerpetual, "XRPUSDT")
    # trade.start()

    startDate = datetime(2022, 1, 4, 0, 0, 0)
    endDate = datetime(2022, 1, 10, 1, 30, 0)
    backTest = BackTest(market.Type.USDTPerpetual, "XRPUSDT", startDate, endDate)
    backTest.start()
