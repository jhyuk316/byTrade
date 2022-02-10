from datetime import datetime
from backTest import BackTest
import market
from byTrade import Trade

if __name__ == "__main__":
    print("Start ByTrade!!!")

    # trade = Trade(market.Type.USDTPerpetual, "XRPUSDT")
    # trade.start()

    # 백테스트
    startDate = datetime(2022, 2, 1, 0, 0, 0)
    endDate = datetime(2022, 2, 10, 12, 00, 0)
    backTest = BackTest(
        market.Type.USDTPerpetual,
        "BTCUSDT",
        startDate,
        endDate,
        quantity=0.001,
        shortMA=6,
        longMA=20,
        tickInterval=3,
    )
    backTest.start()
