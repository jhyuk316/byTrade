from dataclasses import dataclass


@dataclass
class CoinData:
    shortMA: float = None
    longMA: float = None
    shortMAStd: float = None
    longMAStd: float = None
    close: float = None
    open: float = None
    high: float = None
    low: float = None


# TODO ema macd rsi 조사
# 받아올 데이터를 무엇으로 할 것인가?
# 데이터 가공의 역할을 누가 맡을 것인가?


class Strategy:
    def __init__(self, BBFactor: int = 2) -> None:
        self.preData: CoinData = None
        self.curData: CoinData = None
        self.isCrossUpBB = False
        self.isCrossDownBB = False
        self.bollingerBandsFactor = BBFactor
        self._initDecision_()

    def decide(self, coinData: CoinData) -> None:
        self._initDecision_()
        self.preData = self.curData
        self.curData = coinData

        upBB = self.curData.longMA + self.bollingerBandsFactor * self.curData.longMAStd
        downBB = (
            self.curData.longMA - self.bollingerBandsFactor * self.curData.longMAStd
        )

        self.isInBox = True
        if (
            self.curData.longMAStd * self.bollingerBandsFactor
            > self.curData.longMA * 0.005
        ):
            self.isInBox = False

        if self.curData.close >= upBB:
            self.isCrossUpBB = True
        if self.curData.close <= downBB:
            self.isCrossDownBB = True

        if self.isCrossUpBB and self.curData.close < self.curData.shortMA:
            self.isCrossUpBB = False
            self.isCrossDownBB = False
            if not self.isInBox:
                self.allCloseLong = True
                # self.closeLong = True
            else:
                # self.allCloseLong = True
                self.closeLong = True
            self.openShort = True

        if self.isCrossDownBB and self.curData.close > self.curData.shortMA:
            self.isCrossUpBB = False
            self.isCrossDownBB = False
            if not self.isInBox:
                self.allCloseShort = True
                # self.closeShort = True
            else:
                # self.allCloseShort = True
                self.closeShort = True
            self.openLong = True

        self.hold = self._isHold_()

    def _initDecision_(self):
        self.openShort = False
        self.closeShort = False
        self.openLong = False
        self.closeLong = False
        self.allCloseShort = False
        self.allCloseLong = False
        self.hold = True

    def _isHold_(self) -> bool:
        if (
            self.openShort
            or self.closeShort
            or self.openLong
            or self.closeLong
            or self.allCloseLong
            or self.allCloseShort
        ):
            return False
        return True

