# import datetime
import datetime
import os
import time
import pandas as pd
import requests
from tiingo import TiingoClient



time_last_request = time.time()
requests_made = 0

def check_rate_limit_tiingo():
    # Add 1 to the number of requests made
    global requests_made
    global time_last_request
    requests_made += 1
    print(f"Tiingo Requests made: {requests_made}")

    # If 60 seconds have passed since the last request, reset the counter
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
    headers = {"Content-Type": "application/json","Authorization": f"Token {TIINGO_API_KEY}"}
    params = {"startDate": start_date, "endDate": end_date, "resampleFreq": "1min"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    # print(data)
    if not data:
        print(f"No data returned from API for symbol: {symbol}")
        return None

    df = pd.DataFrame(data)
    df['symbol'] = symbol
    df.set_index("date", inplace=True)
    return df

def get_market_regime_data(symbol, period):
    check_rate_limit_tiingo()
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=period)

    url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {TIINGO_API_KEY}"
    }
    params = {
        "startDate": start_date.strftime('%Y-%m-%d'),
        "endDate": end_date.strftime('%Y-%m-%d')
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"API request failed with status code: {response.status_code}")
        return None

    data = response.json()

    df = pd.DataFrame(data)

    df.set_index("date", inplace=True)
    return df



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
    df['date'] = pd.to_datetime(df['date']).dt.tz_convert('UTC')
    df['date'] = df['date'].dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index("date", inplace=True)
    return df


# def get_daily_data_in_chunks(symbol, start_date, end_date, api_key):
    config = {
        'api_key': api_key,
        'session': True
    }
    client = TiingoClient(config)

    delta = datetime.timedelta(days=365)  # One year at a time
    current_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    current_end_date = current_start_date + delta

    dfs = []
    while current_end_date <= datetime.datetime.strptime(end_date, '%Y-%m-%d'):
        historical_prices = client.get_ticker_price(
            symbol,
            fmt='json',
            startDate=current_start_date.strftime('%Y-%m-%d'),
            endDate=current_end_date.strftime('%Y-%m-%d'),
            frequency='daily'
        )

        if historical_prices:
            df = pd.DataFrame(historical_prices)
            dfs.append(df)

        current_start_date += delta
        current_end_date += delta

    # Last chunk
    if current_start_date < datetime.datetime.strptime(end_date, '%Y-%m-%d'):
        historical_prices = client.get_ticker_price(
            symbol,
            fmt='json',
            startDate=current_start_date.strftime('%Y-%m-%d'),
            endDate=end_date,
            frequency='daily'
        )
        if historical_prices:
            df = pd.DataFrame(historical_prices)
            dfs.append(df)

    if dfs:
        df_combined = pd.concat(dfs)
        df_combined['symbol'] = symbol
        df_combined['date'] = pd.to_datetime(df_combined['date'])
        df_combined.set_index("date", inplace=True)
        df_combined = df_combined.drop(columns=['divCash', 'splitFactor', 'symbol'])
        df_combined.to_csv(f"{symbol}.csv")
        return df_combined
    else:
        return None





# def get_5_years_of_minute_data(symbol):
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=365 * 6)

    delta = datetime.timedelta(days=30)
    current_start_date = start_date
    current_end_date = start_date + delta

    dfs = []
    while current_end_date <= end_date:
        check_rate_limit_tiingo()
        df = get_tiingo_data(symbol, current_start_date.strftime('%Y-%m-%d'), current_end_date.strftime('%Y-%m-%d'))
        if df is not None:
            dfs.append(df)

        current_start_date += delta
        current_end_date += delta

    if current_start_date < end_date:
        check_rate_limit_tiingo()
        df = get_tiingo_data(symbol, current_start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if df is not None:
            dfs.append(df)

    if len(dfs) > 0:
        df_combined = pd.concat(dfs)
        return df_combined
    else:
        return None
    
