
import asyncio
from functools import partial
import os
import time
from dotenv import load_dotenv
import pandas as pd
from portfolio import Portfolio
from trading_signals import generate_trading_signals
from data_fetching import check_rate_limit_tiingo, get_tiingo_data, get_daily_data
from data_processing import calculate_technical_indicators, calculate_technical_indicators_daily, get_market_regime
from data_visualization import plot__daily_data, plot_data
from multiprocessing import Pool, current_process, Manager

import signal
import datetime

TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY")

def process_symbol(symbol, start_date, end_date, daily_start_date, TIINGO_API_KEY):

    alpaca_api_key = os.getenv("APCA_API_KEY")
    alpaca_secret_key = os.getenv("APCA_API_SECRET")
    alpaca_base_url = "https://paper-api.alpaca.markets"
    portfolio = Portfolio(alpaca_api_key, alpaca_secret_key, alpaca_base_url)
    while True:
        try:
            for _ in range(3):
                try:
                    clock = portfolio.api.get_clock()
                    break
                except Exception as e:
                    print(f"Exception encountered while getting clock: {e}. Retrying.")
                    time.sleep(5)
            else:
                continue

            if clock.is_open:
                end_date = datetime.datetime.now()

                for _ in range(3):
                    try:
                        check_rate_limit_tiingo()
                        data = get_tiingo_data(symbol, start_date, end_date)
                        check_rate_limit_tiingo()
                        daily_data = get_daily_data(symbol, daily_start_date, end_date, TIINGO_API_KEY)
                        break
                    except Exception as e:
                        print(f"Exception encountered while getting data for {symbol}: {e}. Retrying.")
                        time.sleep(5)
                else:
                    continue

                
                data = calculate_technical_indicators(data)
                daily_data = calculate_technical_indicators_daily(daily_data)

                data = data.fillna(0)
                data = data[data['sma_200'] != 0.0]
                daily_data = daily_data.fillna(0)
                daily_data = daily_data[daily_data['sma_200_daily'] != 0.0]

                # data_for_plot = data.iloc[-100:]
                # daily_data_for_plot = daily_data.iloc[-100:]

                plot_data(data, symbol, './plots/minute_data_plots/')
                plot__daily_data(daily_data, symbol, './plots/daily_data_plots/')
                data.to_csv(f'./data-training/{symbol}_trading_data_full.csv')
                daily_data.to_csv(f'./data-training/{symbol}_daily_trading_data_full.csv')
                data = data.iloc[-1:]
                daily_data = daily_data.iloc[-1:]

                data.to_csv(f'./data/{symbol}_trading_data.csv')
                market_regime = get_market_regime(symbol)
                signals = generate_trading_signals(data, daily_data, portfolio, market_regime)

                signals.to_csv(f'./signals/{symbol}_trading_signals.csv')
                time.sleep(3)

                # portfolio.execute_trade(symbol, signals['signal'].iloc[-1]) 
                signal = signals['signal'].iloc[-1]
                print(f"Finished a trading cycle for {symbol} with the signal: {signal}.")

                loop = asyncio.new_event_loop()
                loop.run_until_complete(portfolio.execute_trade(symbol, signal))
                loop.close()
                time.sleep(60)
            else:
                print("Market is closed.")
                time.sleep(60)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # ignore the SIGINT signal


def main():
    load_dotenv()
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=14)
        daily_start_date = end_date - datetime.timedelta(days=2000)

        symbols = ['BP', 'CTRA', 'KMI', 'CNX', 'NFG', 'ZG', 'CPB', 'NVDA', 'CG', 'AAPL', 'MSFT' ]
        partial_process_symbol = partial(process_symbol, start_date=start_date, end_date=end_date, daily_start_date=daily_start_date, TIINGO_API_KEY=TIINGO_API_KEY)

        with Pool(os.cpu_count(), initializer=init_worker) as p:
            try:
                p.map(partial_process_symbol, symbols)
            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Terminating processes.")
                p.terminate()
                p.join()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()