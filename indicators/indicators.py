from ta.trend import SMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange


def calculate_indicators(symbol, df):

    if df is None or df.empty:
        return None
    
    df = df.copy()

    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    volume = df["Volume"].squeeze()

    # Moving Averages
    df["MA19"] = SMAIndicator(close, window=19).sma_indicator()
    df["MA38"] = SMAIndicator(close, window=38).sma_indicator()
    df["MA209"] = SMAIndicator(close, window=209).sma_indicator()

    # ADX
    adx = ADXIndicator(
        high=high,
        low=low,
        close=close,
        window=14
    )

    df["ADX"] = adx.adx()
    df["DI+"] = adx.adx_pos()
    df["DI-"] = adx.adx_neg()

    # ATR
    atr = AverageTrueRange(
        high=high,
        low=low,
        close=close,
        window=14
    )

    df["ATR"] = atr.average_true_range()

    # Relative Volume
    avg_volume = volume.iloc[:-1].mean()

    if avg_volume > 0:
        df["RVOL"] = volume / avg_volume
    else:
        df["RVOL"] = 0

    # Debug (احذف هذه الأسطر بعد الانتهاء من التشخيص)
    print(f"\n===== {symbol} =====")
    print(df.tail())
    print(df.columns)

    last = df.iloc[-1]
    print("Columns:", df.columns.tolist())
    print("Type Close:", type(df["Close"]))
    print("Close value:")
    print(df["Close"].tail())

    print("Last row:")
    print(last)

    print("last['Close'] =", last["Close"])

    price = float(close.iloc[-1])

    return {
        "symbol": symbol,
        "price": round(price, 2),

        "MA19": round(float(last["MA19"]), 2),
        "MA38": round(float(last["MA38"]), 2),
        "MA209": round(float(last["MA209"]), 2),

        "ADX": round(float(last["ADX"]), 2),
        "DI+": round(float(last["DI+"]), 2),
        "DI-": round(float(last["DI-"]), 2),

        "ATR": round(float(last["ATR"]), 2),

        "RVOL": round(float(last["RVOL"]), 2),
        "Volume": int(last["Volume"])
    }