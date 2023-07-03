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


def generate_basic_conditions(row, portfolio):
    short_positions = portfolio.get_short_positions() if portfolio.get_short_positions() else {}
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
        "portfolio_has_short_position": short_positions.get(row['symbol'], {}).get('shares', 0) < 0,
        "portfolio_no_position": portfolio.positions.get(row['symbol'], {}).get('shares', 0) == 0,

    }

def generate_basic_daily_conditions(row, portfolio):
    short_positions = portfolio.get_short_positions() if portfolio.get_short_positions() else {}

    return{
        # Add daily conditions
        "macd_cross_up_daily": row['macd_daily'] > row['macd_signal_daily'],
        "macd_cross_down_daily": row['macd_daily'] < row['macd_signal_daily'],
        "sma_50_above_200_daily": row['sma_50_daily'] > row['sma_200_daily'],
        "sma_50_below_200_daily": row['sma_50_daily'] < row['sma_200_daily'],
        "rsi_less_than_30_daily": row['rsi_daily'] < 30,
        "rsi_less_than_70_daily": row['rsi_daily'] < 70,
        "rsi_greater_than_70_daily": row['rsi_daily'] > 70,
        "close_less_than_lower_bb_daily": row['close'] < row['lower_bb_daily'],
        "close_greater_than_upper_bb_daily": row['close'] > row['upper_bb_daily'],
        "slowk_less_than_20_daily": row['slowk_daily'] < 20,
        "slowd_less_than_20_daily": row['slowd_daily'] < 20,
        "slowk_greater_than_80_daily": row['slowk_daily'] > 80,
        "slowd_greater_than_80_daily": row['slowd_daily'] > 80,
        "close_greater_than_senkou_span_a_daily": row['close'] > row['senkou_span_a_daily'],
        "senkou_span_a_greater_than_b_daily": row['senkou_span_a_daily'] > row['senkou_span_b_daily'],
        "close_less_than_senkou_span_a_daily": row['close'] < row['senkou_span_a_daily'],
        "close_less_than_senkou_span_b_daily": row['close'] < row['senkou_span_b_daily'],
        "close_in_sma_50_band_daily": (row['close'] > 0.95*row['sma_50_daily']) & (row['close'] < 1.05*row['sma_50_daily']),
        "close_in_fib_0_band_daily": (row['close'] > row['fib_0_daily']) & (row['close'] < row['fib_0.236_daily']),
        "close_in_fib_0.5_band_daily": (row['close'] > row['fib_0.5_daily']) & (row['close'] < row['fib_0.618_daily']),
        "close_in_fib_1_band_daily": (row['close'] > row['fib_0.786_daily']) & (row['close'] < row['fib_1_daily']),
        "close_in_fib_2_band_daily": (row['close'] > row['fib_0.618_daily']) & (row['close'] < row['fib_0.786_daily']),
        "portfolio_has_position": portfolio.positions.get(row['symbol'], {}).get('shares', 0) > 0,
        "portfolio_has_short_position": short_positions.get(row['symbol'], {}).get('shares', 0) < 0,
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

def generate_composite_daily_conditions(basic_conditions):

    return{
        "bullish_cross_daily": basic_conditions["macd_cross_up_daily"] & basic_conditions["sma_50_above_200_daily"],
        "bearish_cross_daily": basic_conditions["macd_cross_down_daily"] & basic_conditions["sma_50_below_200_daily"] & basic_conditions["rsi_greater_than_70_daily"],
        "oversold_condition_daily": basic_conditions["rsi_less_than_30_daily"] & basic_conditions["close_less_than_lower_bb_daily"] & basic_conditions["macd_cross_down_daily"],
        "overbought_condition_daily": basic_conditions["rsi_greater_than_70_daily"] & basic_conditions["close_greater_than_upper_bb_daily"] & basic_conditions["macd_cross_down_daily"],
        "stoch_oversold_daily": basic_conditions["slowk_less_than_20_daily"] & basic_conditions["slowd_less_than_20_daily"] & basic_conditions["close_less_than_lower_bb_daily"] & basic_conditions["rsi_less_than_30_daily"],
        "stoch_overbought_daily": basic_conditions["slowk_greater_than_80_daily"] & basic_conditions["slowd_greater_than_80_daily"] & basic_conditions["close_greater_than_upper_bb_daily"] & basic_conditions["rsi_less_than_70_daily"],
        "bullish_ichimoku_daily": basic_conditions["close_greater_than_senkou_span_a_daily"] & basic_conditions["senkou_span_a_greater_than_b_daily"] & basic_conditions["macd_cross_up_daily"] & basic_conditions["sma_50_above_200_daily"],
        "bearish_ichimoku_daily": basic_conditions["close_less_than_senkou_span_a_daily"] | basic_conditions["close_less_than_senkou_span_b_daily"] & basic_conditions["macd_cross_down_daily"] & basic_conditions["sma_50_below_200_daily"],
        "hold_condition_daily": basic_conditions["close_in_sma_50_band_daily"],
        "cover_signals_fib_daily": basic_conditions["close_in_fib_0_band_daily"] & basic_conditions["macd_cross_up_daily"] & basic_conditions["sma_50_above_200_daily"] & basic_conditions["portfolio_has_short_position"],
        "short_signals_fib_daily": basic_conditions["close_in_fib_1_band_daily"] & basic_conditions["macd_cross_down_daily"] & basic_conditions["sma_50_below_200_daily"] & basic_conditions["portfolio_has_short_position"],
        "buy_signals_fib_daily": basic_conditions["close_in_fib_0_band_daily"] & basic_conditions["macd_cross_up_daily"] & basic_conditions["sma_50_above_200_daily"] & basic_conditions["portfolio_no_position"],
        "sell_signals_fib_daily": basic_conditions["close_in_fib_2_band_daily"] & basic_conditions["macd_cross_down_daily"] & basic_conditions["sma_50_below_200_daily"] & basic_conditions["portfolio_has_position"],
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


def generate_advanced_daily_conditions(basic_conditions, composite_conditions):
    other_daily_conditions = {
        "exit_bullish_daily": composite_conditions["bullish_cross_daily"] & basic_conditions["portfolio_has_position"],
        "exit_bearish_daily": composite_conditions["bearish_cross_daily"] & basic_conditions["portfolio_has_short_position"],
        "advanced_bullish_cross_daily": composite_conditions["bullish_cross_daily"] & basic_conditions["close_in_fib_0_band_daily"],
        "advanced_bearish_cross_daily": composite_conditions["bearish_cross_daily"] & basic_conditions["close_in_fib_2_band_daily"],
        "advanced_bullish_ichimoku_daily": composite_conditions["bullish_ichimoku_daily"] & basic_conditions["close_in_sma_50_band_daily"],
        "advanced_bearish_ichimoku_daily": composite_conditions["bearish_ichimoku_daily"] & basic_conditions["close_in_sma_50_band_daily"],
        "high_risk_bullish_daily": composite_conditions["overbought_condition_daily"] & basic_conditions["portfolio_no_position"],
        "high_risk_bearish_daily": composite_conditions["oversold_condition_daily"] & basic_conditions["portfolio_has_position"],
        "lower_risk_bullish_daily": composite_conditions["stoch_oversold_daily"] & basic_conditions["portfolio_no_position"],
        "lower_risk_bearish_daily": composite_conditions["stoch_overbought_daily"] & basic_conditions["portfolio_has_position"],
    }
    other_daily_conditions_sum = sum(other_daily_conditions.values())
    hold_condition_daily = other_daily_conditions_sum == 0
    return {**other_daily_conditions, "hold_daily": hold_condition_daily}

def generate_trading_signals(df, daily_df, portfolio, market_regime):
    try:
        print(market_regime)
        for i in range(5, len(df)):
            df.loc[i, 'close_price_dropped'] = df.loc[i, 'close'] < df.loc[i - 5, 'close'] * 0.95

        signals = pd.DataFrame(index=df.index)
        signals['symbol'] = df['symbol']
        signals['buy_price'] = 0.0
        signals['num_shares'] = 0
        signals['profit'] = 0.0
        signals['signal'] = 'hold'
        signals['short_sell_price'] = 0.0
        signals['num_shares_shorted'] = 0

        for idx, row in df.iterrows():
            daily_row = daily_df[daily_df.index <= idx].iloc[-1]
            basic_conditions = generate_basic_conditions(row, portfolio)
            composite_conditions = generate_composite_conditions(basic_conditions)
            advanced_conditions = generate_advanced_conditions(basic_conditions, composite_conditions)
            basic_daily_conditions = generate_basic_daily_conditions(daily_row, portfolio)
            composite_daily_conditions = generate_composite_daily_conditions(basic_daily_conditions)
            advanced_daily_conditions = generate_advanced_daily_conditions(basic_daily_conditions, composite_daily_conditions)
            



            weights_by_regime = {
                'bullish': {
                    "advanced_bullish_cross": 4.0,
                    "advanced_bullish_cross_daily": 2.0,  
                    "lower_risk_bullish": 3.5,
                    "lower_risk_bullish_daily": 1.75,  
                    "high_risk_bullish": 2.0,
                    "high_risk_bullish_daily": 1.0,  
                    "advanced_bullish_ichimoku": 3.0,
                    "advanced_bullish_ichimoku_daily": 1.5,  
                    "hold": 1.0,
                },
                'bearish': {
                    "advanced_bearish_cross": 4.0,
                    "advanced_bearish_cross_daily": 2.0,  
                    "high_risk_bearish": 2.0,
                    "high_risk_bearish_daily": 1.0,  
                    "lower_risk_bearish": 3.5,
                    "lower_risk_bearish_daily": 1.75,  
                    "advanced_bearish_ichimoku": 3.0,
                    "advanced_bearish_ichimoku_daily": 1.5,  
                    "hold": 1.0,

                },
                'low_volatility': {
                    "exit_bullish": 4.0,
                    "exit_bullish_daily": 2.0,  
                    "hold": 1.0,
                },
                'high_volatility': {
                    "exit_bearish": 4.0,
                    "exit_bearish_daily": 2.0,  
                    "hold": 1.0,
                }
            }



            # Merge all the conditions
            all_conditions = {**basic_conditions, **composite_conditions, **advanced_conditions, **basic_daily_conditions, **composite_daily_conditions, **advanced_daily_conditions}

            weights = weights_by_regime.get(market_regime, {})
            # conditions_for_actions = {key: [key] for key in all_conditions.keys()}

            actions_to_conditions = {
                "buy": [
                    "advanced_bullish_cross", 
                    "advanced_bullish_cross_daily", 
                    "lower_risk_bullish", 
                    "lower_risk_bullish_daily", 
                    "high_risk_bullish", 
                    "high_risk_bullish_daily", 
                    "advanced_bullish_ichimoku",
                    "advanced_bullish_ichimoku_daily"
                ],
                "sell": [
                    "advanced_bearish_cross", 
                    "advanced_bearish_cross_daily", 
                    "lower_risk_bearish", 
                    "lower_risk_bearish_daily", 
                    "high_risk_bearish", 
                    "high_risk_bearish_daily", 
                    "advanced_bearish_ichimoku",
                    "advanced_bearish_ichimoku_daily",
                ],
                "short": [
                    "high_risk_bearish", 
                    "high_risk_bearish_daily", 
                    "advanced_bearish_ichimoku", 
                    "advanced_bearish_ichimoku_daily", 
                    "lower_risk_bearish",
                    "lower_risk_bearish_daily"
                ],
                "cover": [
                    "high_risk_bullish", 
                    "high_risk_bullish_daily", 
                    "advanced_bullish_ichimoku", 
                    "advanced_bullish_ichimoku_daily", 
                    "lower_risk_bullish",
                    "lower_risk_bullish_daily"
                ],
                "hold": [
                    "exit_bullish", 
                    "exit_bullish_daily", 
                    "exit_bearish", 
                    "exit_bearish_daily", 
                    "hold"
                ]
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




