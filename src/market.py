# USDT Perpetual

from enum import Enum


class Type(Enum):
    InversePerpetual = 1
    USDTPerpetual = 2
    InverseFutures = 3
    Spot = 4


class TradeType(Enum):
    MAIN = 1
    TEST = 2


class URL:
    def __init__(self, marketType: Type, tradeType: TradeType = TradeType.TEST):
        if marketType == Type.InversePerpetual:
            pass
        elif marketType == Type.USDTPerpetual:
            if tradeType == TradeType.TEST:
                self.urlRestBybit = "http://api-testnet.bybit.com"
                self.urlWebSocketPublic = (
                    "wss://stream-testnet.bybit.com/realtime_public"
                )
                self.urlWebSocketPrivate = (
                    "wss://stream-testnet.bybit.com/realtime_private"
                )
            elif tradeType == TradeType.MAIN:
                self.urlRestBybit = "http://api.bybit.com"
                self.urlWebSocketPublic = "wss://stream.bybit.com/realtime_public"
                self.urlWebSocketPrivate = "wss://stream.bybit.com/realtime_private"
            else:
                Exception("Wrong Trade Type")
        elif marketType == Type.InverseFutures:
            pass
        elif marketType == Type.Spot:
            pass
        else:
            Exception("Wrong Market Type")
