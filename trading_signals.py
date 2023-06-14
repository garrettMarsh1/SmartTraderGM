# Required Libraries
import time
import requests
import os
import pandas as pd
import numpy as np
import talib
import traceback
import asyncio

time_last_request = time.time()
requests_made = 0
def check_rate_limit_tiingo():
    # Add 1 to the number of requests made
    global requests_made
    global time_last_request
    requests_made += 1
    print(f"Tiingo Requests made: {requests_made}")

    # If 60 seconds have passed since the last request reset the counter
    if time.time() - time_last_request >= 60:
        requests_made = 0
        time_last_request = time.time()
    elif requests_made >= 200:  # If the limit is hit, sleep for 60 seconds
        print("Rate limit hit! Waiting 60 seconds...")
        time.sleep(60)
        requests_made = 0
        time_last_request = time.time()


# Tiingo API Key
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY")

def get_tiingo_data(symbol, start_date, end_date):
    url = f"https://api.tiingo.com/iex/{symbol}/prices"
    headers = {"Content-Type": "application/json","Authorization": f"Token {'6ceb439fce674f4b793a7ff074b9ca443d1c79bf'}"}
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

def generate_basic_conditions(row, portfolio):
    return {
        "macd_cross_up": row['macd'] > row['macd_signal'],
        "macd_cross_down": row['macd'] < row['macd_signal'],
        "sma_50_above_200": row['sma_50'] > row['sma_200'],
        "sma_50_below_200": row['sma_50'] < row['sma_200'],
        "rsi_less_than_30": row['rsi'] < 30,
        "rsi_less_than_70": row['rsi'] < 70,
        "rsi_greater_than_70": row['rsi'] > 70,
        "close_less_than_lower_bb": row['close'] < row['lower_bb'],
        "close_greater_than_upper_bb": row['close'] > row['upper_bb'],
        "slowk_less_than_20": row['slowk'] < 20,
        "slowd_less_than_20": row['slowd'] < 20,
        "slowk_greater_than_80": row['slowk'] > 80,
        "slowd_greater_than_80": row['slowd'] > 80,
        "close_greater_than_senkou_span_a": row['close'] > row['senkou_span_a'],
        "senkou_span_a_greater_than_b": row['senkou_span_a'] > row['senkou_span_b'],
        "close_less_than_senkou_span_a": row['close'] < row['senkou_span_a'],
        "close_less_than_senkou_span_b": row['close'] < row['senkou_span_b'],
        "close_in_sma_50_band": (row['close'] > 0.95*row['sma_50']) & (row['close'] < 1.05*row['sma_50']),
        "close_in_fib_0_band": (row['close'] > row['fib_0']) & (row['close'] < row['fib_0.236']),
        "close_in_fib_0.5_band": (row['close'] > row['fib_0.5']) & (row['close'] < row['fib_0.618']),
        "close_in_fib_1_band": (row['close'] > row['fib_0.786']) & (row['close'] < row['fib_1']),
        "close_in_fib_2_band": (row['close'] > row['fib_0.618']) & (row['close'] < row['fib_0.786']),
        "portfolio_has_position": portfolio.positions.get(row['symbol'], {}).get('shares', 0) > 0,
        "portfolio_has_short_position": portfolio.get_short_positions().get(row['symbol'], {}).get('shares', 0) < 0,
        "portfolio_no_position": portfolio.positions.get(row['symbol'], {}).get('shares', 0) == 0,
    }

def generate_composite_conditions(basic_conditions):
    return {
        "bullish_cross": basic_conditions["macd_cross_up"] & basic_conditions["sma_50_above_200"],
        "oversold_condition": basic_conditions["rsi_less_than_30"] & basic_conditions["close_less_than_lower_bb"] & basic_conditions["macd_cross_down"],
        "stoch_oversold": basic_conditions["slowk_less_than_20"] & basic_conditions["slowd_less_than_20"] & basic_conditions["close_less_than_lower_bb"] & basic_conditions["rsi_less_than_30"],
        "bullish_ichimoku": basic_conditions["close_greater_than_senkou_span_a"] & basic_conditions["senkou_span_a_greater_than_b"] & basic_conditions["macd_cross_up"] & basic_conditions["sma_50_above_200"],
        "bearish_cross": basic_conditions["macd_cross_down"] & basic_conditions["sma_50_below_200"] & basic_conditions["rsi_greater_than_70"],
        "overbought_condition": basic_conditions["rsi_greater_than_70"] & basic_conditions["close_greater_than_upper_bb"] & basic_conditions["macd_cross_down"],
        "stoch_overbought": basic_conditions["slowk_greater_than_80"] & basic_conditions["slowd_greater_than_80"] & basic_conditions["close_greater_than_upper_bb"] & basic_conditions["rsi_less_than_70"],
        "bearish_ichimoku": basic_conditions["close_less_than_senkou_span_a"] | basic_conditions["close_less_than_senkou_span_b"] & basic_conditions["macd_cross_down"] & basic_conditions["sma_50_below_200"],
        "hold_condition": basic_conditions["close_in_sma_50_band"],
        "cover_signals_fib": basic_conditions["close_in_fib_0_band"] & basic_conditions["macd_cross_up"] & basic_conditions["sma_50_above_200"] & basic_conditions["portfolio_has_short_position"],
        "short_signals_fib": basic_conditions["close_in_fib_1_band"] & basic_conditions["macd_cross_down"] & basic_conditions["sma_50_below_200"] & basic_conditions["portfolio_has_short_position"],
        "buy_signals_fib": basic_conditions["close_in_fib_0_band"] & basic_conditions["macd_cross_up"] & basic_conditions["sma_50_above_200"] & basic_conditions["portfolio_no_position"],
        "sell_signals_fib": basic_conditions["close_in_fib_2_band"] & basic_conditions["macd_cross_down"] & basic_conditions["sma_50_below_200"] & basic_conditions["portfolio_has_position"],
    }

def generate_advanced_conditions(basic_conditions, composite_conditions):
    other_conditions = {
        "advanced_bullish_cross": composite_conditions["bullish_cross"] & basic_conditions["close_in_fib_0_band"],
        "advanced_bearish_cross": composite_conditions["bearish_cross"] & basic_conditions["close_in_fib_2_band"],
        "advanced_bullish_ichimoku": composite_conditions["bullish_ichimoku"] & basic_conditions["close_in_sma_50_band"],
        "advanced_bearish_ichimoku": composite_conditions["bearish_ichimoku"] & basic_conditions["close_in_sma_50_band"],
        "high_risk_bullish": composite_conditions["overbought_condition"] & basic_conditions["portfolio_no_position"],
        "high_risk_bearish": composite_conditions["oversold_condition"] & basic_conditions["portfolio_has_position"],
        "lower_risk_bullish": composite_conditions["stoch_oversold"] & basic_conditions["portfolio_no_position"],
        "lower_risk_bearish": composite_conditions["stoch_overbought"] & basic_conditions["portfolio_has_position"],
        "exit_bullish": composite_conditions["bullish_cross"] & basic_conditions["portfolio_has_position"],
        "exit_bearish": composite_conditions["bearish_cross"] & basic_conditions["portfolio_has_short_position"],
    }
    other_conditions_sum = sum(other_conditions.values())
    hold_condition = other_conditions_sum == 0
    return {**other_conditions, "hold": hold_condition}


def generate_trading_signals(df, portfolio, market_regime):
    try:
        print(market_regime)
        
        signals = pd.DataFrame(index=df.index)
        signals['symbol'] = df['symbol']
        signals['buy_price'] = 0.0
        signals['num_shares'] = 0
        signals['profit'] = 0.0
        signals['signal'] = 'hold'
        signals['short_sell_price'] = 0.0
        signals['num_shares_shorted'] = 0

        for idx, row in df.iterrows():
            basic_conditions = generate_basic_conditions(row, portfolio)
            composite_conditions = generate_composite_conditions(basic_conditions)
            advanced_conditions = generate_advanced_conditions(basic_conditions, composite_conditions)


            weights_by_regime = {
                'bullish': {
                    "advanced_bullish_cross": 4.0,
                    "lower_risk_bullish": 3.5,
                    "high_risk_bullish": 2.0,
                    "advanced_bullish_ichimoku": 3.0,
                    "hold": 1.0,
                },
                'bearish': {
                    "advanced_bearish_cross": 4.0,
                    "high_risk_bearish": 2.0,
                    "lower_risk_bearish": 3.5,
                    "advanced_bearish_ichimoku": 3.0,
                    "hold": 1.0,
                },
                'low_volatility': {
                    "exit_bullish": 4.0,
                    "hold": 1.0,
                },
                'high_volatility': {
                    "exit_bearish": 4.0,
                    "hold": 1.0,
                }
            }



            # Merge all the conditions
            all_conditions = {**basic_conditions, **composite_conditions, **advanced_conditions}

            weights = weights_by_regime.get(market_regime, {})
            # conditions_for_actions = {key: [key] for key in all_conditions.keys()}

            actions_to_conditions = {
                "buy": ["advanced_bullish_cross", "lower_risk_bullish", "high_risk_bullish", "advanced_bullish_ichimoku"],
                "sell": ["advanced_bearish_cross", "lower_risk_bearish", "high_risk_bearish", "advanced_bearish_ichimoku"],
                "short": ["high_risk_bearish", "advanced_bearish_ichimoku", "lower_risk_bearish"],
                "cover": ["high_risk_bullish", "advanced_bullish_ichimoku", "lower_risk_bullish"],
                "hold": ["exit_bullish", "exit_bearish", "hold"]
            }


            scores = {action: sum(weights.get(condition, 0) * all_conditions[condition] for condition in actions_to_conditions[action]) for action in actions_to_conditions}

            if all(value == 0 for value in scores.values()):
                scores['hold'] = 3.0

            # Now modify scores based on portfolio conditions for this row
            if portfolio.positions.get(row['symbol'], {}).get('shares', 0) <= 0:
                scores['sell'] = 0.0

            if portfolio.positions.get(row['symbol'], {}).get('shares', 0) > 0:
                scores['short'] = 0.0

            if portfolio.positions.get(row['symbol'], {}).get('short_shares', 0) <= 0:
                scores['cover'] = 0.0
            max_score_action = max(scores, key=lambda action: scores[action])


            print(scores)
            if row['symbol'] in portfolio.positions:
                print(portfolio.positions[row['symbol']]['shares'])


            if max_score_action == "buy" and portfolio.buying_power > df.at[idx, 'close']:
                
                signals.at[idx, 'signal'] = 'buy'
                signals.at[idx, 'buy_price'] = df.at[idx, 'close']
                signals.at[idx, 'num_shares'] = portfolio.buying_power // signals.at[idx, 'buy_price']
                signals.at[idx, 'profit'] = signals.at[idx, 'num_shares'] * (df.at[idx, 'close'] - signals.at[idx, 'buy_price'])
            
            elif max_score_action == "short":

                signals.at[idx, 'signal'] = 'short'
                signals.at[idx, 'short_sell_price'] = df.at[idx, 'close']
                signals.at[idx, 'num_shares_shorted'] = portfolio.buying_power // signals.at[idx, 'short_sell_price']
                signals.at[idx, 'profit'] = signals.at[idx, 'num_shares_shorted'] * (signals.at[idx, 'short_sell_price'] - df.at[idx, 'close'])

            elif max_score_action == "sell" and portfolio.positions.get(row['symbol'], {}).get('shares', 0) > 0:
                signals.at[idx, 'signal'] = 'sell'
                signals.at[idx, 'buy_price'] = df.at[idx, 'close']
                signals.at[idx, 'num_shares'] = portfolio.positions.get(row['symbol'], 0)
                signals.at[idx, 'profit'] = signals.at[idx, 'num_shares'] * (signals.at[idx, 'buy_price'] - df.at[idx, 'close'])

            elif max_score_action == "cover" and row['symbol'] in portfolio.get_short_positions():
                signals.at[idx, 'signal'] = 'cover'
                signals.at[idx, 'short_sell_price'] = df.at[idx, 'close']
                signals.at[idx, 'num_shares_shorted'] = portfolio.get_short_positions().get(row['symbol'], 0)
                signals.at[idx, 'profit'] = signals.at[idx, 'num_shares_shorted'] * (df.at[idx, 'close'] - signals.at[idx, 'short_sell_price'])

            elif max_score_action == "hold":
                print("holding")
                signals.at[idx, 'signal'] = 'hold'

            print(f"For date {idx}, the chosen action is for {row['symbol']}: {max_score_action}")

        # Fill NaN with 0
        signals.fillna(0, inplace=True)

        return signals
    except Exception as e:
        traceback.print_exc()




