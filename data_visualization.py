import time
from matplotlib import dates
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import timedelta

import requests

from trading_signals import calculate_technical_indicators, check_rate_limit_tiingo
from mplfinance.original_flavor import candlestick_ohlc


def plot_data(df, symbol, output_dir):
    # Convert the index to datetime
    df.index = pd.to_datetime(df.index, unit='ns')  # Change is here
    df = df.tail(100)

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a figure and multiple subplots
    fig, axs = plt.subplots(5, figsize=(14, 7*7))

    non_zero_mask = (df['senkou_span_a'] != 0) & (df['senkou_span_b'] != 0)
    lower_y_limit = min(df.loc[non_zero_mask, ['senkou_span_a', 'senkou_span_b']].min())
    upper_y_limit = max(df.loc[non_zero_mask, ['senkou_span_a', 'senkou_span_b']].max())

    # Plot price and moving averages
    # axs[0].scatter(df[df['macd'] > df['macd_signal']].index, df[df['macd'] > df['macd_signal']]['close'], color='g', marker='^', alpha=1)
    # axs[0].scatter(df[df['macd'] < df['macd_signal']].index, df[df['macd'] < df['macd_signal']]['close'], color='r', marker='v', alpha=1)
    axs[0].fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=df['senkou_span_a']>=df['senkou_span_b'], color='lightgreen', alpha=0.5, label='Senkou Span A >= Senkou Span B')
    axs[0].fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=df['senkou_span_a']<df['senkou_span_b'], color='lightcoral', alpha=0.5, label='Senkou Span A < Senkou Span B')
    min_close = df['close'].min()
    max_close = df['close'].max()
    # axs[0].set_xlim([df.index[0], df.index[-22]]) 
    axs[0].set_ylim([min_close, max_close])
    axs[0].plot(df['close'], label='Close')
    axs[0].plot(df['sma_50'], label='SMA 50')
    axs[0].plot(df['sma_200'], label='SMA 200')
    axs[0].set_title(f'{symbol} - Price and Moving Averages')
    axs[0].legend()

    # Plot Bollinger Bands
    axs[1].fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=df['senkou_span_a']>=df['senkou_span_b'], color='lightgreen', alpha=0.5, label='Senkou Span A >= Senkou Span B')
    axs[1].fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=df['senkou_span_a']<df['senkou_span_b'], color='lightcoral', alpha=0.5, label='Senkou Span A < Senkou Span B')
    # axs[1].set_xlim([df.index[0], df.index[-22]])  # Adjusting x-axis to remove the last 22 rows
    # axs[1].set_ylim([lower_y_limit, upper_y_limit])  # Adjusting y-axis based on non-zero values
    # axs[1].scatter(df[df['sma_50'] > df['sma_200']].index, df[df['sma_50'] > df['sma_200']]['close'], color='g', marker='^', alpha=1)
    # axs[1].scatter(df[df['sma_50'] < df['sma_200']].index, df[df['sma_50'] < df['sma_200']]['close'], color='r', marker='v', alpha=1)
    axs[1].plot(df['close'], label='Close')
    axs[1].plot(df['upper_bb'], label='Upper BB')
    axs[1].plot(df['middle_bb'], label='Middle BB')
    axs[1].plot(df['lower_bb'], label='Lower BB')
    axs[1].set_title(f'{symbol} - Bollinger Bands')
    y_min = df['close'].min()
    y_max = df['close'].max()
    axs[1].set_ylim(y_min, y_max)
    axs[1].legend()

    # Plot RSI

    axs[2].plot(df['rsi'], label='RSI')
    axs[2].axhline(y=30, color='green', linestyle='--')
    axs[2].axhline(y=70, color='red', linestyle='--')
    axs[2].set_title(f'{symbol} - RSI')
    axs[2].legend()

    # Plot MACD

    axs[3].plot(df['macd'], label='MACD')
    axs[3].plot(df['macd_signal'], label='Signal')
    axs[3].set_title(f'{symbol} - MACD')
    axs[3].legend()


    # Plot Fibonacci Levels
    axs[4].plot(df['close'], label='Close')
    fib_levels = ['fib_0', 'fib_0.236', 'fib_0.382', 'fib_0.5', 'fib_0.618', 'fib_0.786', 'fib_1']
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']
    for level, color in zip(fib_levels, colors):
        axs[4].plot(df[level], label=level, color=color)
        if level != 'fib_1':
            next_level = fib_levels[fib_levels.index(level)+1]
            axs[4].fill_between(df.index, df[level], df[next_level], color=color, alpha=0.1)

    # Set the y-axis limits based on the maximum and minimum values of the close column
    y_min = df['close'].min()
    y_max = df['close'].max()
    axs[4].set_ylim(y_min, y_max)

    axs[4].set_title(f'{symbol} - Fibonacci Levels')
    axs[4].legend()



    # Set common labels
    for ax in axs:
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.grid(True)

    # Save the plot to the output directory
    plt.savefig(os.path.join(output_dir, f'{symbol}_stock_indicators_plot.png'))
    plt.close(fig)  # Close the figure to free up memory






# Tiingo API Key
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY")


from tiingo import TiingoClient

def get_daily_data(symbol, start_date, end_date, api_key):
    config = {
        'api_key': api_key,
        'session': True
    }
    client = TiingoClient(config)
    historical_prices = client.get_ticker_price(
        symbol,
        fmt='json',
        startDate=start_date,
        endDate=end_date,
        frequency='daily'
    )

    df = pd.DataFrame(historical_prices)
    df['symbol'] = symbol
    df['date'] = pd.to_datetime(df['date'])
    df.set_index("date", inplace=True)
    return df


symbols = ['NVDA', 'CG', 'LIN', 'AAPL', 'MSFT', 'BSTZ', 'BMEZ', 'BST', 'ARES', 'BME', 'COLD']

for symbol in symbols:
    data = get_daily_data(symbol, '2023-05-01', '2023-06-14', TIINGO_API_KEY)

    data = calculate_technical_indicators(data)

    # data = data[data['sma_200'] != 0.0]

    #drop divCash
    data = data.drop(columns=['divCash'])
    #drop splitFactor
    data = data.drop(columns=['splitFactor'])

    data = data.drop(columns=['symbol'])

    # print(data)
    #plot the data form nvda
    plot_data(data, symbol, './plots/')
# # Tiingo API Key
# TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY")

# def get_tiingo_data(symbol, start_date, end_date):
#     check_rate_limit_tiingo()
#     url = f"https://api.tiingo.com/iex/{symbol}/prices"
#     headers = {"Content-Type": "application/json","Authorization": f"Token {TIINGO_API_KEY}"}
#     params = {"startDate": start_date, "endDate": end_date, "resampleFreq": "1min"}
#     response = requests.get(url, headers=headers, params=params)
#     data = response.json()
    
#     if not data:
#         print(f"No data returned from API for symbol: {symbol}")
#         return None
    
#     df = pd.DataFrame(data)
#     df['symbol'] = symbol
#     df['date'] = pd.to_datetime(df['date'])
#     df.set_index("date", inplace=True)
#     return df

    



# symbols = ['BP', 'NTR', 'CTRA', 'KMI', 'CNX', 'NFG', 'ZG']

# # Get the data for each symbol
# for symbol in symbols:
#     data = get_tiingo_data(symbol, '2023-06-09', '2023-06-10')
#     data = calculate_technical_indicators(data)
#     data = data.fillna(0)
#     data = data[data['sma_200'] != 0.0]
#     #only the most recent half of the data
#     data = data.tail(int(len(data)/2))


#     # Plot the data
#     plot_data(data, symbol, './plots/daily_data_plots')






