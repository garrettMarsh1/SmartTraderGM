# Required Libraries
import requests
import os
import pandas as pd
import numpy as np
import talib
import traceback


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



        # for idx, row in df.iterrows():


    # Choose action with highest score and generate signal accordingly
        

        # Choose action with highest score and generate signal accordingly
        for idx, row in df.iterrows():

            conditions = {
                "bullish_cross": (row['macd'] > row['macd_signal']) & (row['sma_50'] > row['sma_200']),
                "oversold_condition": (row['rsi'] < 30) & (row['close'] < row['lower_bb']) & (row['macd'] < row['macd_signal']),
                "stoch_oversold": (row['slowk'] < 20) & (row['slowd'] < 20) & (row['close'] < row['lower_bb']) & (row['rsi'] >= 30),
                "bullish_ichimoku": (row['close'] > row['senkou_span_a']) & (row['senkou_span_a'] > row['senkou_span_b']) & (row['macd'] > row['macd_signal']) & (row['sma_50'] > row['sma_200']),
                "bearish_cross": (row['macd'] < row['macd_signal']) & (row['sma_50'] < row['sma_200']) & (row['rsi'] > 70),
                "overbought_condition": (row['rsi'] > 70) & (row['close'] > row['upper_bb']) & (row['macd'] < row['macd_signal']),
                "stoch_overbought": (row['slowk'] > 80) & (row['slowd'] > 80) & (row['close'] > row['upper_bb']) & (row['rsi'] <= 70),
                "bearish_ichimoku": (row['close'] < row['senkou_span_a']) | (row['close'] < row['senkou_span_b']) & (row['macd'] < row['macd_signal']) & (row['sma_50'] < row['sma_200']),
                "cover_signals_fib": (row['close'] > row['fib_0']) & (row['close'] < row['fib_0.236']) & (row['macd'] > row['macd_signal']) & (row['sma_50'] > row['sma_200']),
                "hold_condition": (row['close'] > 0.95*row['sma_50']) & (row['close'] < 1.05*row['sma_50']),
                "cover_signals_fib": (row['close'] > row['fib_0']) & (row['close'] < row['fib_0.236']) & (row['macd'] > row['macd_signal']) & (row['sma_50'] > row['sma_200']) & (portfolio.get_short_positions().get(row['symbol'], {}).get('shares', 0) > 0),
                "short_signals_fib": (row['close'] > row['fib_0.786']) & (row['close'] < row['fib_1']) & (row['macd'] < row['macd_signal']) & (row['sma_50'] < row['sma_200']) & (portfolio.get_short_positions().get(row['symbol'], {}).get('shares', 0) < 0),
                "buy_signals_fib": (row['close'] > row['fib_0']) & (row['close'] < row['fib_0.236']) & (row['macd'] > row['macd_signal']) & (row['sma_50'] > row['sma_200']) & (portfolio.positions.get(row['symbol'], {}).get('shares', 0) == 0),
                "sell_signals_fib": (row['close'] > row['fib_0.618']) & (row['close'] < row['fib_0.786']) & (row['macd'] < row['macd_signal']) & (row['sma_50'] < row['sma_200']) & (portfolio.positions.get(row['symbol'], {}).get('shares', 0) > 0),

                }
            # Define weights for each market regime
            weights_by_regime = {
                'bullish': {
                    "bullish_cross": 2.5,
                    "oversold_condition": 2.0, 
                    "stoch_oversold": 1.5,  
                    "bullish_ichimoku": 3.5,  
                    "buy_signals_fib": 2.5,  
                },
                'bearish': {
                    "bearish_cross": 2.6,  
                    "overbought_condition": 2.1,
                    "stoch_overbought": 1.4,  
                    "bearish_ichimoku": 3.7,  
                    "sell_signals_fib": 2.4,  
                },
                'low_volatility': {
                    "hold_condition": 3.5,
                },
                'high_volatility': {
                    "short_signals_fib": 2.8,  
                    "cover_signals_fib": 2.8,  
                }
            }

            # Get weights for current market regime
            weights = weights_by_regime.get(market_regime, {})

        


            # Compute scores for each action

            conditions_for_actions = {
                "buy": ["bullish_cross", "oversold_condition", "stoch_oversold", "bullish_ichimoku", "buy_signals_fib"],
                "sell": ["bearish_cross", "overbought_condition", "stoch_overbought", "bearish_ichimoku", "sell_signals_fib"],
                "short": ["bearish_cross", "overbought_condition", "stoch_overbought", "bearish_ichimoku", "short_signals_fib"],
                "cover": ["bullish_cross", "oversold_condition", "stoch_oversold", "bullish_ichimoku", "cover_signals_fib"],
                "hold": ["hold_condition"]
            }

            # Calculate scores for this row
            scores = {action: sum(weights.get(condition, 0) * conditions[condition] for condition in conditions_for_action) for action, conditions_for_action in conditions_for_actions.items()}

    



            #if all scores are zero set to hold
            if all(value == 0 for value in scores.values()):
                scores['hold'] = 3.0


            # # Choose the action for this row
            
            # # Now modify scores based on portfolio conditions for this row
            if portfolio.positions.get(row['symbol'], {}).get('shares', 0) <= 0:
                scores['sell'] = 0.0

            if portfolio.positions.get(row['symbol'], {}).get('shares', 0) > 0:
                scores['short'] = 0.0
                
            if portfolio.positions.get(row['symbol'], {}).get('shares', 0) >= 0:
                scores['cover'] = 0.0

            max_score_action = max(scores, key=lambda action: scores[action])
            # print(portfolio.positions.get(row['symbol'], {}).get('shares', 0))
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




