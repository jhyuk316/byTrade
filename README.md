# byTrade

## 개요

byBit API(pybit 모듈)를 활용해 알고리즘 트레이딩을 하는 프로그램.

## 요구사항

- python 3.7 이상
- pybit

## 파라미터 정의 및 해석

### side

- Buy
- Sell

### symbol

- BTCUSDT
- ...

### order_type

- Limit - 메이커
- Market - 테이커

### qty

### close_on_trigger

### reduce_only

### Time in force (time_in_force)

- 시장가(market)
  - GoodTillCancel - 취소할 때가지 유요한 주문
  - ImmediateOrCancel - 지정가에 주문을 입력후, 즉시 체결이 안되면 해당 주문을 취소
  - FillOrKill - 지정가에 주문을 입력후 원하는 수량이 모두 체결이 안되면 주문을 취소.
- 메이커(limit)
  - PostOnly - 메이커 온니
