
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
    # portfolio.manage_risk()
    # portfolio.update_positions()
    # portfolio.optimize_portfolio()
    

    # Get start and end dates
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=7)
    # start_date = datetime.datetime(2023, 6, 2)

    symbols = ['CG', 'ARES', 'BX', 'ALC', 'BSTZ', 'COLD', 'ET', 'FLEX', 'MX', 'MRK', 'GE', 'LIN', 'LMT', 'NOC', 'RTX', 'TSLA', 'WMT', 'ZM', 'NVDA', 'MSFT', 'AAPL', 'GOOGL']

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
                    df = calculate_technical_indicators(df)
                    df_json = data.to_json(orient='split')
                    socket.emit('chart_data', df_json)
                    #fill na with 0 for data
                    data = data.fillna(0)
                    data = data[data['sma_200'] != 0.0]
                    data = data.iloc[-1]
                    #send data to csv
                    data.to_csv(f'./data/{symbol}_trading_data.csv')
                    market_regime = portfolio.get_market_regime(symbol)
                    signals = generate_trading_signals(data, portfolio, market_regime)
                    signals.to_csv(f'./signals/{symbol}_trading_signals.csv')

                    portfolio.execute_trade(symbol, signals['signal'].iloc[-1]) 
                
                print("Finished a trading cycle.")
                print(portfolio.positions)
                # portfolio.manage_risk()
                time.sleep(60)
                
            else:
                
                print("Market is closed.")
                print(f"Next market open is: {clock.next_open}")
                print(portfolio.positions)
                time.sleep(3600)
                
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()




# def get_secrets(**kwargs):
#     secret = {}
#     secret['username'] = Variable.get(secret_name, defaulkt_bar = 'undefined', deserialize_json = True)['username']
#     secret['password'] = Variable.get(secret_name, defaulkt_bar = 'undefined', deserialize_json = True)['password']
#     secret['url'] = Variable.get(secret_name, defaulkt_bar = 'undefined', deserialize_json = True)['url']
#     return secret

# def check_jobs(context):
#     secret = context['secret']

#     ...logic to check jobs...

# .... DAG code ...

# get_secret = PythonOperator(
#     task_id = 'get_secret',
#     python_callable = get_secrets,
#     provide_context=True)

# check_jobs = PythonOperator(
#     task_id = 'check_jobs',
#     python_callable = check_jobs,
#     provide_context=True,
#     op_args = ['xcom_pull(task_ids = "get_secret", key = "secret")']
#     )

                                                                                                        
