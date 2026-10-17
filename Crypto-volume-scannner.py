import requests
import time
from datetime import datetime, timezone

# MARKET VOLUME SCANNER
# Binance Top 50 USDT Coins

BASE_URL = "https://api.binance.com"

TIMEFRAMES = ["15m", "1h", "4h", "1d"]

TOP_COINS = 50

MIN_PREVIOUS_CANDLES = 2

MAX_PREVIOUS_CANDLES = 200

SCAN_INTERVAL = 60

seen_alerts = set()


def get_top_coins():
    url = BASE_URL + "/api/v3/ticker/24hr"

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    data = response.json()

    coins = []

    for coin in data:
        symbol = coin["symbol"]

        if not symbol.endswith("USDT"):
            continue

        if symbol.endswith(("UPUSDT", "DOWNUSDT",
                            "BULLUSDT", "BEARUSDT")):
            continue

        coins.append(coin)

    coins.sort(
        key=lambda x: float(x["quoteVolume"]),
        reverse=True
    )

    return [coin["symbol"] for coin in coins[:TOP_COINS]]


def get_candles(symbol, timeframe):
    url = BASE_URL + "/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": timeframe,
        "limit": MAX_PREVIOUS_CANDLES + 2
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def check_volume(symbol, timeframe):

    candles = get_candles(symbol, timeframe)

    now = int(time.time() * 1000)

    closed = [
        candle for candle in candles
        if int(candle[6]) < now
    ]

    if len(closed) < MIN_PREVIOUS_CANDLES + 1:
        return

    current = closed[-1]

    current_volume = float(current[5])

    previous = closed[:-1]

    count = 0

    for candle in reversed(previous):

        old_volume = float(candle[5])

        if current_volume > old_volume:
            count += 1
        else:
            break

    if count < MIN_PREVIOUS_CANDLES:
        return

    candle_id = current[6]

    alert_id = (symbol, timeframe, candle_id)

    if alert_id in seen_alerts:
        return

    seen_alerts.add(alert_id)

    open_price = float(current[1])
    high_price = float(current[2])
    low_price = float(current[3])
    close_price = float(current[4])

    upper_wick = high_price - max(
        open_price, close_price
    )

    lower_wick = min(
        open_price, close_price
    ) - low_price

    if lower_wick > upper_wick:
        signal = "BUY POSSIBILITY"

    elif upper_wick > lower_wick:
        signal = "SELL POSSIBILITY"

    else:
        signal = "NEUTRAL"

    print("\n========================")

    print("MARKET VOLUME ALERT")

    print("Coin:", symbol)

    print("Timeframe:", timeframe)

    print("Volume:", current_volume)

    print("Previous lower-volume candles:", count)

    print("Signal:", signal)

    print("Candle closed:",
          datetime.fromtimestamp(
              candle_id / 1000,
              tz=timezone.utc
          ).isoformat())

    print("========================\n")


def run_scanner():

    print("Market Volume Scanner Started")

    while True:

        try:
            coins = get_top_coins()

            for symbol in coins:

                for timeframe in TIMEFRAMES:

                    try:
                        check_volume(
                            symbol,
                            timeframe
                        )

                    except Exception as error:
                        print(
                            "Error:",
                            symbol,
                            timeframe,
                            error
                        )

                    time.sleep(0.15)

        except Exception as error:
            print("Scanner Error:", error)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    run_scanner()
