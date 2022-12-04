from datetime import datetime
from backTest import BackTest
import market
from byTrade import Trade
from pybit import usdt_perpetual

if __name__ == "__main__":
    print("Start ByTrade!!!")

    trade = Trade(
        marketType=market.Type.USDTPerpetual,
        symbol="XRPUSDT",
        shortMA=18,
        longMA=60,
        BBFactor=2,
        tickInterval=1,
        quantity=1,
        tradeType=market.TradeType.MAIN)
    trade.start()
    # trade.run()

    # 백테스트
    # startDate = datetime(2022, 2, 10, 12, 0, 0)
    # endDate = datetime(2022, 2, 11, 21, 10, 0)
    # backTest = BackTest(
    #     market.Type.USDTPerpetual,
    #     "BTCUSDT",
    #     startDate,
    #     endDate,
    #     quantity=0.001,
    #     shortMA=6,
    #     longMA=20,
    #     tickInterval=3,
    # )
    # backTest.start()
    # backTest.run()
