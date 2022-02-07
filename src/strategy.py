from dataclasses import dataclass
from enum import Enum


@dataclass
class CoinData:
    shortMA: float = None
    longMA: float = None
    shortMA: float = None
    longMAStd: float = None
    close: float = None
    open: float = None
    high: float = None
    low: float = None


class Decision(Enum):
    openShort = 1
    closeShort = 2
    openLong = 3
    closeLong = 4
    hold = 5


# TODO RSI 조사
# 받아올 데이터를 무엇으로 할 것인가?
# 데이터 가공의 역할을 누가 맡을 것인가?


class Strategy:
    def __init__(self, BBFactor: int = 2) -> None:
        self.preData: CoinData = None
        self.curData: CoinData = None
        self.isCrossUpBB = False
        self.isCrossDownBB = False
        self.bollingerBandsFactor = BBFactor

    def decide(self, coinData: CoinData) -> Decision:
        self.preData = self.curData
        self.curData = coinData

        upBB = self.curData.longMA + self.bollingerBandsFactor * self.curData.longMAStd
        downBB = (
            self.curData.longMA - self.bollingerBandsFactor * self.curData.longMAStd
        )

        isInBox = True
        if (
            self.curData.longMAStd * self.bollingerBandsFactor
            > self.curData.longMA * 0.005
        ):
            isInBox = False

        if self.curData.close >= upBB:
            self.isCrossUpBB = True

        if self.curData.close <= downBB:
            self.isCrossDownBB = True

        if self.isCrossUpBB and self.curData.close < self.curData.shortMA:
            self.isCrossUpBB = False
            self.isCrossDownBB = False
            return Decision.openShort

        if self.isCrossDownBB and self.curData.close > self.curData.shortMA:
            self.isCrossUpBB = False
            self.isCrossDownBB = False
            return Decision.closeShort

        return Decision.hold
