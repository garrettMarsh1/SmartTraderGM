import time
from matplotlib import dates
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import timedelta
import mplfinance as mpf
from data_fetching import get_tiingo_data, get_daily_data


def plot_data(df, symbol, output_dir):
    # Convert the index to datetime
    df.index = pd.to_datetime(df.index, unit='ns')  # Change is here
    df = df.tail(150)


    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    fig, axs = plt.subplots(6, figsize=(14, 7*7))
    market_colors = mpf.make_marketcolors(up='tab:green', down='tab:red', volume='inherit', ohlc='inherit')
    mpf_style = mpf.make_mpf_style(base_mpl_style="seaborn", marketcolors=market_colors)







    # Plot price and moving averages
    axs[0].scatter(df[df['macd'] > df['macd_signal']].index, df[df['macd'] > df['macd_signal']]['close'], color='g', marker='^', alpha=1)
    axs[0].scatter(df[df['macd'] < df['macd_signal']].index, df[df['macd'] < df['macd_signal']]['close'], color='r', marker='v', alpha=1)
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
    axs[1].plot(df['close'], label='Close')
    axs[1].plot(df['upper_bb'], label='Upper BB')
    axs[1].plot(df['middle_bb'], label='Middle BB')
    axs[1].plot(df['lower_bb'], label='Lower BB')
    axs[1].set_title(f'{symbol} - Bollinger Bands')
    y_min = df['lower_bb'].min()
    y_max = df['upper_bb'].max()
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

    # Plot Candlestick
    ohlc = df[['open', 'high', 'low', 'close']]
    
# Calculate the max value in the 'high' column and add 5 to it
    max_high = df['high'].max()
    max_low = df['low'].min()
    mpf.plot(ohlc, type='candle', ax=axs[5], show_nontrading=True, style=mpf_style)
    axs[5].set_title(f'{symbol} - Candlestick Chart')
    axs[5].fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=df['senkou_span_a'] >= df['senkou_span_b'], color='lightgreen', alpha=0.5, label='Senkou Span A >= Senkou Span B')
    axs[5].fill_between(df.index, df['senkou_span_a'], df['senkou_span_b'], where=df['senkou_span_a'] < df['senkou_span_b'], color='lightcoral', alpha=0.5, label='Senkou Span A < Senkou Span B')

    axs[5].grid(True)
    axs[5].set_ylim(top=max_high, bottom=max_low)

    for ax in axs[:-1]:  # Exclude last ax which is handled by mplfinance
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.grid(True)

    # Save the plot to the output directory
    plt.savefig(os.path.join(output_dir, f'{symbol}_stock_indicators_plot.png'))
    plt.close(fig)  # Close the figure to free up memory




def plot__daily_data(df_daily, symbol, output_dir):
    # Convert the index to datetime
    df_daily.index = pd.to_datetime(df_daily.index, unit='ns')  # Change is here
    df_daily = df_daily.tail(100)


    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a figure and multiple subplots
    fig, axs = plt.subplots(6, figsize=(14, 7*7))
    market_colors = mpf.make_marketcolors(up='tab:green', down='tab:red', volume='inherit', ohlc='inherit')
    mpf_style = mpf.make_mpf_style(base_mpl_style="seaborn", marketcolors=market_colors)





    # Plot price and moving averages
    axs[0].scatter(df_daily[df_daily['macd_daily'] > df_daily['macd_signal_daily']].index, df_daily[df_daily['macd_daily'] > df_daily['macd_signal_daily']]['close'], color='g', marker='^', alpha=1)
    axs[0].scatter(df_daily[df_daily['macd_daily'] < df_daily['macd_signal_daily']].index, df_daily[df_daily['macd_daily'] < df_daily['macd_signal_daily']]['close'], color='r', marker='v', alpha=1)
    axs[0].fill_between(df_daily.index, df_daily['senkou_span_a_daily'], df_daily['senkou_span_b_daily'], where=df_daily['senkou_span_a_daily']>=df_daily['senkou_span_b_daily'], color='lightgreen', alpha=0.5, label='Senkou Span A >= Senkou Span B')
    axs[0].fill_between(df_daily.index, df_daily['senkou_span_a_daily'], df_daily['senkou_span_b_daily'], where=df_daily['senkou_span_a_daily']<df_daily['senkou_span_b_daily'], color='lightcoral', alpha=0.5, label='Senkou Span A < Senkou Span B')
    min_close = df_daily['close'].min()
    max_close = df_daily['close'].max()
    # axs[0].set_xlim([df_daily.index[0], df_daily.index[-22]]) 
    axs[0].set_ylim([min_close, max_close])
    axs[0].plot(df_daily['close'], label='Close')
    axs[0].plot(df_daily['sma_50_daily'], label='SMA 50')
    axs[0].plot(df_daily['sma_200_daily'], label='SMA 200')
    axs[0].set_title(f'{symbol} - Price and Moving Averages')
    axs[0].legend()

    # Plot Bollinger Bands
    axs[1].fill_between(df_daily.index, df_daily['senkou_span_a_daily'], df_daily['senkou_span_b_daily'], where=df_daily['senkou_span_a_daily']>=df_daily['senkou_span_b_daily'], color='lightgreen', alpha=0.5, label='Senkou Span A >= Senkou Span B')
    axs[1].fill_between(df_daily.index, df_daily['senkou_span_a_daily'], df_daily['senkou_span_b_daily'], where=df_daily['senkou_span_a_daily']<df_daily['senkou_span_b_daily'], color='lightcoral', alpha=0.5, label='Senkou Span A < Senkou Span B')
    axs[1].plot(df_daily['close'], label='Close')
    axs[1].plot(df_daily['upper_bb_daily'], label='Upper BB')
    axs[1].plot(df_daily['middle_bb_daily'], label='Middle BB')
    axs[1].plot(df_daily['lower_bb_daily'], label='Lower BB')
    axs[1].set_title(f'{symbol} - Bollinger Bands')
    y_min = df_daily['lower_bb_daily'].min()
    y_max = df_daily['upper_bb_daily'].max()
    axs[1].set_ylim(y_min, y_max)
    axs[1].legend()

    # Plot RSI

    axs[2].plot(df_daily['rsi_daily'], label='RSI')
    axs[2].axhline(y=30, color='green', linestyle='--')
    axs[2].axhline(y=70, color='red', linestyle='--')
    axs[2].set_title(f'{symbol} - RSI')
    axs[2].legend()

    # Plot MACD

    axs[3].plot(df_daily['macd_daily'], label='MACD')
    axs[3].plot(df_daily['macd_signal_daily'], label='Signal')
    axs[3].set_title(f'{symbol} - MACD')
    axs[3].legend()


    # Plot Fibonacci Levels
    axs[4].plot(df_daily['close'], label='Close')
    fib_levels = ['fib_0_daily', 'fib_0.236_daily', 'fib_0.382_daily', 'fib_0.5_daily', 'fib_0.618_daily', 'fib_0.786_daily', 'fib_1_daily']
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']
    for level, color in zip(fib_levels, colors):
        axs[4].plot(df_daily[level], label=level, color=color)
        if level != 'fib_1_daily':
            next_level = fib_levels[fib_levels.index(level)+1]
            axs[4].fill_between(df_daily.index, df_daily[level], df_daily[next_level], color=color, alpha=0.1)

    # Set the y-axis limits based on the maximum and minimum values of the close column
    y_min = df_daily['close'].min()
    y_max = df_daily['close'].max()
    axs[4].set_ylim(y_min, y_max)

    axs[4].set_title(f'{symbol} - Fibonacci Levels')
    axs[4].legend()

    # Plot Candlestick

    ohlc = df_daily[['open', 'high', 'low', 'close']]
    
    mpf.plot(ohlc, type='candle', ax=axs[5], show_nontrading=True, style=mpf_style)
    max_high = df_daily['high'].max()
    axs[5].set_ylim(top=max_high)
    axs[5].fill_between(df_daily.index, df_daily['senkou_span_a_daily'], df_daily['senkou_span_b_daily'], where=df_daily['senkou_span_a_daily'] >= df_daily['senkou_span_b_daily'], color='lightgreen', alpha=0.5, label='Senkou Span A >= Senkou Span B')
    axs[5].fill_between(df_daily.index, df_daily['senkou_span_a_daily'], df_daily['senkou_span_b_daily'], where=df_daily['senkou_span_a_daily'] < df_daily['senkou_span_b_daily'], color='lightcoral', alpha=0.5, label='Senkou Span A < Senkou Span B')

    axs[5].set_title(f'{symbol} - Candlestick Chart')
    axs[5].grid(True)

    for ax in axs[:-1]:  # Exclude last ax which is handled by mplfinance
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.grid(True)


    # Save the plot to the output directory
    plt.savefig(os.path.join(output_dir, f'{symbol}_stock_indicators_plot.png'))
    plt.close(fig)  # Close the figure to free up memory







