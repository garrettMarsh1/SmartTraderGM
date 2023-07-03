import numpy as np
import talib
import time
import requests
import os
import pandas as pd

from data_fetching import  get_market_regime_data


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

def calculate_ichimoku_daily(df):
    high_prices = df['high']
    close_prices = df['close']
    low_prices = df['low']

    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    period9_high = high_prices.rolling(window=9).max()
    period9_low = low_prices.rolling(window=9).min()
    df['tenkan_sen_daily'] = (period9_high + period9_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
    period26_high = high_prices.rolling(window=26).max()
    period26_low = low_prices.rolling(window=26).min()
    df['kijun_sen_daily'] = (period26_high + period26_low) / 2

    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
    df['senkou_span_a_daily'] = ((df['tenkan_sen_daily'] + df['kijun_sen_daily']) / 2).shift(26)

    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
    period52_high = high_prices.rolling(window=52).max()
    period52_low = low_prices.rolling(window=52).min()
    df['senkou_span_b_daily'] = ((period52_high + period52_low) / 2).shift(26)

    # The most current closing price plotted 22 time periods behind (optional)
    df['chikou_span_daily'] = close_prices.shift(-22)

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

def fibonacci_retracement_daily(df):
    # Calculate the rolling high and low for the full period
    df['rolling_high'] = df['high'].rolling(window=len(df), min_periods=1).max()
    df['rolling_low'] = df['low'].rolling(window=len(df), min_periods=1).min()

    # Calculate the difference between the high and low
    diff = df['rolling_high'] - df['rolling_low']
    
    # Calculate Fibonacci levels and store them in the DataFrame
    levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    for level in levels:
        df[f'fib_{level}_daily'] = df['rolling_high'] - diff * level

    # Drop the rolling high and low as they're no longer needed
    df = df.drop(columns=['rolling_high', 'rolling_low'])

    return df



# Function to Calculate Technical Indicators including Ichimoku cloud
def calculate_technical_indicators_daily(df):
    # df.rename(columns={'close':'close', 'high':'high', 'low':'low', 'open': 'open_daily', }, inplace=True)
    close = np.array(df['close'], dtype='f8')
    high = np.array(df['high'], dtype='f8')
    low = np.array(df['low'], dtype='f8')

    #rename close high and low to close, high, low
    

    # Calculate Technical Indicators
    df['sma_50_daily'] = talib.SMA(close, timeperiod=50)
    df['sma_200_daily'] = talib.SMA(close, timeperiod=200)
    df['upper_bb_daily'], df['middle_bb_daily'], df['lower_bb_daily'] = talib.BBANDS(close, timeperiod=20)
    df['rsi_daily'] = talib.RSI(close, timeperiod=14)
    df['macd_daily'], df['macd_signal_daily'], df['macd_hist_daily'] = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df['slowk_daily'], df['slowd_daily'] = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    df['adx_daily'] = talib.ADX(high, low, close, timeperiod=14)
    df['cci_daily'] = talib.CCI(high, low, close, timeperiod=14)
    
    # Calculate Ichimoku cloud components
    df = calculate_ichimoku_daily(df)
    df = fibonacci_retracement_daily(df)
    
    # Fill NaN values with 0
    df.fillna(0, inplace=True)
    
    return df


def get_market_regime(symbol, short_period=10, long_period=20, adx_period=14, atr_period=14):
        
    required_period = max(long_period+1000, adx_period+1000, atr_period+1000)
    market_data = get_market_regime_data(symbol, period=required_period)
    market_data['symbol'] = symbol

    close = market_data['close']
    high = market_data['high']
    low = market_data['low']

    short_sma = talib.SMA(close, timeperiod=short_period)
    long_sma = talib.SMA(close, timeperiod=long_period)
    adx = talib.ADX(high, low, close, timeperiod=adx_period)
    atr = talib.ATR(high, low, close, timeperiod=atr_period)

    sma_trend = (short_sma > long_sma).astype(int) - (short_sma < long_sma).astype(int)

    market_data = market_data.assign(
        short_sma=short_sma,
        long_sma=long_sma,
        adx=adx,
        atr=atr,
        sma_trend=sma_trend,
    )

    atr_threshold = 1.5 * atr.median()
    market_data['median_atr'] = atr.median()

    market_data.to_csv(f'./market_regime_data/{symbol}_market_regime.csv')
    #fill with 0s
    market_data = market_data.fillna(0)

    last_sma_trend = sma_trend.iat[-1]
    last_adx = adx.iat[-1]
    last_atr = atr.iat[-1]

    if last_sma_trend > 0 and last_adx > 25:
        return 'bullish'
    elif last_sma_trend < 0 and last_adx > 25:
        return 'bearish'
    elif last_atr < atr_threshold:
        return 'low_volatility'
    else:
        return 'high_volatility'


