
import datetime
import os
import socket
import time
from dotenv import load_dotenv
import pandas as pd
from portfolio import Portfolio
from trading_signals import calculate_technical_indicators, generate_trading_signals, get_tiingo_data


def main():
    # Load environment variables
    load_dotenv()

    # Initialize API keys and credentials
    alpaca_api_key = os.getenv("APCA_API_KEY")
    alpaca_secret_key = os.getenv("APCA_API_SECRET")
    alpaca_base_url = "https://paper-api.alpaca.markets"

    # Initialize portfolio
    portfolio = Portfolio(alpaca_api_key, alpaca_secret_key, alpaca_base_url)

    # print the portfolio positions
    print(portfolio.positions)

    short_positions = portfolio.get_short_positions()
    print(short_positions)


    # Get start and end dates
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=5)
    # start_date = datetime.datetime(2023, 6, 2)

    symbols = ['NTR', 'ZG', 'CTRA']


    while True:
        try:
            # Get the current market status
            for _ in range(3):  # Attempt the operation 3 times
                try:
                    clock = portfolio.api.get_clock()
                    break  # Break the loop if the operation was successful
                except Exception as e:
                    print(f"Exception encountered while getting clock: {e}. Retrying.")
                    time.sleep(5)  # Wait for 5 seconds before retrying
            else:
                continue  # Continue to the next iteration of the main loop if we weren't able to get the clock

            # If the market is open, execute trades
            if clock.is_open:
                # Update end date
                end_date = datetime.datetime.now()

                for symbol in symbols:
                    for _ in range(3):  # Attempt the operation 3 times
                        try:
                            # Get the latest minute data
                            data = get_tiingo_data(symbol, start_date, end_date)
                            break  # Break the loop if the operation was successful
                        except Exception as e:
                            print(f"Exception encountered while getting data for {symbol}: {e}. Retrying.")
                            time.sleep(5)  # Wait for 5 seconds before retrying
                    else:
                        continue  # Continue to the next symbol if we weren't able to get the data
                    

                    data = calculate_technical_indicators(data)


                    data = data.fillna(0)
                    data = data[data['sma_200'] != 0.0]
                    data = data.iloc[-1:]
                    #send data to csv
                    data.to_csv(f'./data/{symbol}_trading_data.csv')
                    market_regime = portfolio.get_market_regime(symbol)
                    signals = generate_trading_signals(data, portfolio, market_regime)
                    signals.to_csv(f'./signals/{symbol}_trading_signals.csv')
                    time.sleep(1)
                    portfolio.execute_trade(symbol, signals['signal'].iloc[-1]) 
                
                print("Finished a trading cycle.")
                print(portfolio.positions)
                
                time.sleep(60)
                
            else:
                
                print("Market is closed.")
                print(f"Next market open is: {clock.next_open}")
                print(portfolio.positions)

                time.sleep(60)
                
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()



                                                                                                        
