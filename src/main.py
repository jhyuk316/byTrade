import market
from byTrade import Trade

if __name__ == "__main__":
    print("hello")

    trade = Trade(market.Type.USDTPerpetual, market.TradeType.MAIN, "XRPUSDT")
    trade.start()
