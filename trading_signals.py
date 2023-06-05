# Required Libraries
import requests
import os
import pandas as pd
import numpy as np
import talib

# Tiingo API Key
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY")

def get_tiingo_data(symbol, start_date, end_date):
    url = f"https://api.tiingo.com/iex/{symbol}/prices"
    headers = {"Content-Type": "application/json","Authorization": f"Token {TIINGO_API_KEY}"}
    params = {"startDate": start_date, "endDate": end_date, "resampleFreq": "1min"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if not data:
        print(f"No data returned from API for symbol: {symbol}")
        return None
    
    df = pd.DataFrame(data)
    df['symbol'] = symbol
    df.set_index("date", inplace=True)
    return df





def calculate_ichimoku(df):
    high_prices = df['high']
    close_prices = df['close']
    low_prices = df['low']

    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    period9_high = high_prices.rolling(window=9).max()
    period9_low = low_prices.rolling(window=9).min()
    df['tenkan_sen'] = (period9_high + period9_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
    period26_high = high_prices.rolling(window=26).max()
    period26_low = low_prices.rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2

    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)

    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
    period52_high = high_prices.rolling(window=52).max()
    period52_low = low_prices.rolling(window=52).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)

    # The most current closing price plotted 22 time periods behind (optional)
    df['chikou_span'] = close_prices.shift(-22)

    # Return dataframe with Ichimoku components
    return df

def fibonacci_retracement(df):
    # Calculate the rolling high and low for the full period
    df['rolling_high'] = df['high'].rolling(window=len(df), min_periods=1).max()
    df['rolling_low'] = df['low'].rolling(window=len(df), min_periods=1).min()

    # Calculate the difference between the high and low
    diff = df['rolling_high'] - df['rolling_low']
    
    # Calculate Fibonacci levels and store them in the DataFrame
    levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    for level in levels:
        df[f'fib_{level}'] = df['rolling_high'] - diff * level

    # Drop the rolling high and low as they're no longer needed
    df = df.drop(columns=['rolling_high', 'rolling_low'])

    return df



# Function to Calculate Technical Indicators including Ichimoku cloud
def calculate_technical_indicators(df):
    close = np.array(df['close'], dtype='f8')
    high = np.array(df['high'], dtype='f8')
    low = np.array(df['low'], dtype='f8')

    # Calculate Technical Indicators
    df['sma_50'] = talib.SMA(close, timeperiod=50)
    df['sma_200'] = talib.SMA(close, timeperiod=200)
    df['upper_bb'], df['middle_bb'], df['lower_bb'] = talib.BBANDS(close, timeperiod=20)
    df['rsi'] = talib.RSI(close, timeperiod=14)
    df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df['slowk'], df['slowd'] = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    df['adx'] = talib.ADX(high, low, close, timeperiod=14)
    df['cci'] = talib.CCI(high, low, close, timeperiod=14)
    
    # Calculate Ichimoku cloud components
    df = calculate_ichimoku(df)
    df = fibonacci_retracement(df)
    
    # Fill NaN values with 0
    df.fillna(0, inplace=True)
    
    return df

def generate_trading_signals(df, portfolio, market_regime):

    print(market_regime)
    # Create a DataFrame to store the trading signals
    signals = pd.DataFrame(index=df.index)
    signals['symbol'] = df['symbol']

    # Add additional columns for the buy price and number of shares owned
    signals['buy_price'] = 0.0
    signals['num_shares'] = 0
    signals['profit'] = 0.0
    signals['signal'] = 'hold'

    bullish_cross = (df['macd'] > df['macd_signal']) & (df['sma_50'] > df['sma_200'])
    oversold_condition = (df['rsi'] < 30) & (df['close'] < df['lower_bb'])
    stoch_oversold = (df['slowk'] < 20) & (df['slowd'] < 20) & (df['close'] < df['lower_bb'])
    bullish_ichimoku = (df['close'] > df['senkou_span_a']) & (df['senkou_span_a'] > df['senkou_span_b'])
    buy_signals_fib = (df['close'] > df['fib_0']) & (df['close'] < df['fib_0.236'])

    bearish_cross = (df['macd'] < df['macd_signal']) & (df['sma_50'] < df['sma_200'])
    overbought_condition = (df['rsi'] > 70) & (df['close'] > df['upper_bb'])
    stoch_overbought = (df['slowk'] > 80) & (df['slowd'] > 80) & (df['close'] > df['upper_bb'])
    bearish_ichimoku = (df['close'] < df['senkou_span_a']) | (df['close'] < df['senkou_span_b'])
    sell_signals_fib = (df['close'] > df['fib_0.786']) & (df['close'] < df['fib_1'])


    # Count the total number of buy and sell conditions
    buy_conditions = [bullish_cross, oversold_condition, bullish_ichimoku, buy_signals_fib, stoch_oversold]
    sell_conditions = [bearish_cross, overbought_condition, bearish_ichimoku, sell_signals_fib, stoch_overbought]
    total_buy = sum(condition.any() for condition in buy_conditions)
    total_sell = sum(condition.any() for condition in sell_conditions)
    # print(f"current buying power: {portfolio.buying_power}")


    # Generate the overall signal
    if total_buy > total_sell and portfolio.buying_power > df['close'].mean():
        signals['signal'] = 'buy'
        signals['buy_price'] = df['close'].mean()
        signals['num_shares'] = portfolio.buying_power // signals['buy_price']
        signals['profit'] = signals['num_shares'] * (df['close'].mean() - signals['buy_price'])
        # print(f"Generated signal: {signals['signal'].values[0]} for symbol {signals['symbol'].values[0]}")

    elif total_sell > total_buy and any(symbol in portfolio.positions for symbol in df['symbol']):
        signals['signal'] = 'sell'
        signals['buy_price'] = df['close'].mean()
        signals['num_shares'] = portfolio.positions[df['symbol'].any()]
        signals['profit'] = signals['num_shares'] * (signals['buy_price'] - df['close'].mean())
        # print(f"Generated signal: {signals['signal'].values[0]} for symbol {signals['symbol'].values[0]}")

    else:
        signals['signal'] = 'hold'
        print(f"Generated signal: {signals['signal'].values[0]} for symbol {signals['symbol'].values[0]}")
        
    #fill NaN with 0
    signals.fillna(0, inplace=True)

    return signals







    # # Different conditions based on the market_regime
    # if market_regime == 'bullish':
    #     print('bullish market')
    #     buy_signals = bullish_cross | oversold_condition | bullish_ichimoku | buy_signals_fib | stoch_oversold
    #     sell_signals = bearish_cross | overbought_condition | bearish_ichimoku | sell_signals_fib | stoch_overbought
    # elif market_regime == 'bearish':
    #     print('bearish market')
    #     buy_signals = bullish_cross & oversold_condition & bullish_ichimoku & buy_signals_fib & stoch_oversold
    #     sell_signals = bearish_cross | overbought_condition | bearish_ichimoku | sell_signals_fib | stoch_overbought
    # elif market_regime == 'low_volatility':
    #     print('low volatility market')
    #     # Prefer range trading strategies for low volatility
    #     buy_signals = oversold_condition | stoch_oversold
    #     sell_signals = overbought_condition | stoch_overbought
    # else:  # 'high_volatility'
    #     print('high volatility market')
    #     # Prefer breakout strategies for high volatility
    #     buy_signals = bullish_cross | bullish_ichimoku
    #     sell_signals = bearish_cross | bearish_ichimoku