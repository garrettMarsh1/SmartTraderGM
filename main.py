import datetime
import os
import time
from alpaca_trade_api.stream import Stream
from datetime import date, timedelta
import numpy as np
import pandas as pd
from data_visualization import plot_data
from portfolio import Portfolio
import asyncio as asyncio
from trading_signals import calculate_technical_indicators, check_rate_limit_tiingo, generate_trading_signals, get_tiingo_data
from config import SYMBOL


def place_order(profit_price, loss_price):
    data = {
        "symbol": SYMBOL,
        "qty": 1,
        "side": "buy",
        "type": "market",
        "time_in_force": "gtc",
        "order_class": "bracket",
        "take_profit": {
            "limit_price": profit_price
        },
        "stop_loss": {
            "stop_price": loss_price
        }
    }

def check_candlestick_pattern(candlesticks):
    if len(candlesticks) > 3:
        last_candle = candlesticks[-2]
        previous_candle = candlesticks[-3]
        first_candle = candlesticks[-4]

        if last_candle['close'] > previous_candle['close'] and previous_candle['close'] > first_candle['close']:
            distance = last_candle['close'] - first_candle['open']
            profit_price = last_candle['close'] + (distance * 2)
            loss_price = first_candle['open']

            return ("place_order", profit_price, loss_price)

    return ("hold",)

def execute_scalping_strategy(data, symbol, portfolio):
    """
    Function to execute scalping strategy. 

    data: Dataframe of the current data
    symbol: The symbol of the stock
    portfolio: Portfolio object for executing trades

    """
    # convert DataFrame to a list of dictionaries
    candlesticks = data.tail(3).to_dict('records')

    action, *args = check_candlestick_pattern(candlesticks)
    # print(action, args, candlesticks)

    
    if action == "place_order":
        print("Place order with profit_price {}, loss_price {}".format(*args))
        place_order(*args)
    elif action == "hold":
        print("Hold signal for {}".format(symbol))



def create_bar_handler(historical_data, bar_data, portfolio):
    async def handle_bar(bar):

        timestamp = datetime.datetime.utcfromtimestamp(bar.timestamp / 1e9)  # divide by 1e9 to convert ns to seconds
        timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'  # format as a string

        new_data = pd.DataFrame({
            'date': [timestamp_str],
            'open': [bar.open],
            'high': [bar.high],
            'low': [bar.low],
            'close': [bar.close],
            'symbol': [bar.symbol],
        })
        new_data['date'] = pd.to_datetime(new_data['date'])
        new_data.set_index('date', inplace=True)

        # Check if new_data's index is in historical_data's index
        if new_data.index[0] in historical_data[bar.symbol].index:
            # Append unique suffix to avoid overwriting
            new_data.index = new_data.index + pd.Timedelta(nanoseconds=1)

    
        bar_data[bar.symbol] = pd.concat([historical_data[bar.symbol], new_data])
        bar_data[bar.symbol] = calculate_technical_indicators(bar_data[bar.symbol])
        bar_data[bar.symbol].to_csv(f'data-training/{bar.symbol}_data.csv')
        #make data_for_plot the most recent 100 rows of bar_data
        data_for_plot = bar_data[bar.symbol].iloc[-50:]
        plot_data(data_for_plot, bar.symbol, './plots/')

        data = bar_data[bar.symbol].fillna(0)
        data = data[data['sma_200'] != 0.0]
        latest_data = data.iloc[-1:]
        market_regime = portfolio.get_market_regime(bar.symbol)
        signals = generate_trading_signals(latest_data, portfolio, market_regime)
        await asyncio.sleep(1)
        # execute_scalping_strategy(bar_data[symbol], symbol, portfolio)
        # execute_scalping_strategy(bar_data[bar.symbol], bar.symbol, portfolio)

        portfolio.execute_trade(bar.symbol, signals['signal'].iloc[-1])
        
    return handle_bar

def main():
    alpaca_api_key = os.getenv("APCA_API_KEY")
    alpaca_secret_key = os.getenv("APCA_API_SECRET")
    alpaca_base_url = "https://paper-api.alpaca.markets"
    portfolio = Portfolio(alpaca_api_key, alpaca_secret_key, alpaca_base_url)
    symbols = ['CG', 'LIN', 'AAPL', 'MSFT', 'BSTZ', 'BMEZ', 'BST', 'ARES', 'BME', 'COLD']
    bar_data = {symbol: pd.DataFrame() for symbol in symbols}
    historical_data = {symbol: pd.DataFrame() for symbol in symbols}
    start_date = (date.today() - timedelta(days=14)).strftime('%Y-%m-%d')
    end_date = date.today().strftime('%Y-%m-%d')
    for stock in symbols:
        check_rate_limit_tiingo()
        df = get_tiingo_data(stock, start_date, end_date)
        if df is not None:
            historical_data[stock] = df
    stream = Stream(
        alpaca_api_key,
        alpaca_secret_key,
        base_url=alpaca_base_url,
        data_feed='iex'  # use 'sip' for paid subscription
    )
    for symbol in symbols:
        handler = create_bar_handler(historical_data, bar_data, portfolio)
        stream.subscribe_bars(handler, symbol)

    stream.run()

if __name__ == "__main__":
    main()


                                                                                                        

# import datetime
# import os
# import time
# from dotenv import load_dotenv
# import pandas as pd
# from portfolio import Portfolio
# from trading_signals import calculate_technical_indicators, generate_trading_signals, get_tiingo_data
# from data_visualization import plot_data


# # Call the function with your data and output directory
    



# def main():
#     # Load environment variables
#     load_dotenv()

#     # Initialize API keys and credentials
#     alpaca_api_key = os.getenv("APCA_API_KEY")
#     alpaca_secret_key = os.getenv("APCA_API_SECRET")
#     alpaca_base_url = "https://paper-api.alpaca.markets"

#     # Initialize portfolio
#     portfolio = Portfolio(alpaca_api_key, alpaca_secret_key, alpaca_base_url)

#     # print the portfolio positions
#     print(portfolio.positions)

#     short_positions = portfolio.get_short_positions()
#     print(short_positions)


#     # Get start and end dates
#     end_date = datetime.datetime.now()
#     start_date = end_date - datetime.timedelta(days=14)
#     # start_date = datetime.datetime(2023, 6, 2)

#     symbols = ['BP', 'CTRA', 'KMI', 'CNX', 'NFG', 'ZG', 'LIN', 'CG', 'ALC', 'CPB', ]

#     while True:
#         try:
#             # Get the current market status
#             for _ in range(3):  # Attempt the operation 3 times
#                 try:
#                     clock = portfolio.api.get_clock()
#                     break  # Break the loop if the operation was successful
#                 except Exception as e:
#                     print(f"Exception encountered while getting clock: {e}. Retrying.")
#                     time.sleep(5)  # Wait for 5 seconds before retrying
#             else:
#                 continue  # Continue to the next iteration of the main loop if we weren't able to get the clock

#             # If the market is open, execute trades
#             if clock.is_open:
#                 # Update end date
#                 end_date = datetime.datetime.now()

#                 for symbol in symbols:
#                     for _ in range(3):  # Attempt the operation 3 times
#                         try:
#                             # Get the latest minute data
#                             data = get_tiingo_data(symbol, start_date, end_date)
#                             break  # Break the loop if the operation was successful
#                         except Exception as e:
#                             print(f"Exception encountered while getting data for {symbol}: {e}. Retrying.")
#                             time.sleep(5)  # Wait for 5 seconds before retrying
#                     else:
#                         continue  # Continue to the next symbol if we weren't able to get the data
                    

#                     data = calculate_technical_indicators(data)


#                     data = data.fillna(0)
#                     data = data[data['sma_200'] != 0.0]
                    
#                     #subtract 1 from data_for_plot to add a row to the data_for_plot each time the loop finishes data_for_plot = data.iloc[-240:]
#                     data_for_plot = data.iloc[-100:]
                    

#                     plot_data(data_for_plot, symbol, './plots/')
#                     data.to_csv(f'./data-training/{symbol}_trading_data_full.csv')
#                     data = data.iloc[-1:]
#                     #send data to csv
#                     data.to_csv(f'./data/{symbol}_trading_data.csv')
#                     market_regime = portfolio.get_market_regime(symbol)
#                     signals = generate_trading_signals(data, portfolio, market_regime)
#                     signals.to_csv(f'./signals/{symbol}_trading_signals.csv')
#                     time.sleep(1)
#                     portfolio.execute_trade(symbol, signals['signal'].iloc[-1]) 
                
#                 print("Finished a trading cycle.")
#                 print(portfolio.positions)
                
#                 time.sleep(60)
                
#             else:
                
#                 print("Market is closed.")
#                 print(f"Next market open is: {clock.next_open}")
#                 print(portfolio.positions)

#                 time.sleep(60)
                
#         except Exception as e:
#             print(f"An unexpected error occurred: {e}")


# if __name__ == "__main__":
#     main()



                                                                                                        
