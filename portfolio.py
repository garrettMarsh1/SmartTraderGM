import datetime
from datetime import timedelta, datetime
import time
import alpaca_trade_api as tradeapi
from matplotlib import pyplot as plt
import numpy as np
import requests
from sklearn.preprocessing import MinMaxScaler
from trading_signals import generate_trading_signals
import talib
import os


import pandas as pd
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY")


class Portfolio:
    def __init__(self, api_key, secret_key, base_url):
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
        self.positions = {}
        # Add the buying power as an attribute that you update every time a buy or sell happens
        self.buying_power = float(self.api.get_account().buying_power)

        # Initialize rate limiter
        self.requests_made = 0
        self.time_last_request = time.time()

        # Initialize portfolio with existing positions
        self.update_positions()
        

    def check_rate_limit(self):
        # Add 1 to the number of requests made
        self.requests_made += 1
        print(f"Requests made: {self.requests_made}")

        # If 60 seconds have passed since the last request reset the counter
        if time.time() - self.time_last_request >= 60:
            self.requests_made = 0
            self.time_last_request = time.time()
        elif self.requests_made >= 200:  # If the limit is hit, sleep for 60 seconds
            print("Rate limit hit! Waiting 60 seconds...")
            time.sleep(60)
            self.requests_made = 0
            self.time_last_request = time.time()

    def update_positions(self):
            # Before every API request, check the rate limit
            self.check_rate_limit()
            # Then make the request
            account = self.api.get_account()
            positions = self.api.list_positions()

            # get the latest trade prices for all symbols at once and store it in a dict
            latest_prices = {pos.symbol: float(self.api.get_latest_trade(pos.symbol).price) for pos in positions}

            for position in positions:
                symbol = position.symbol
                shares = float(position.qty)
                buy_price = float(position.avg_entry_price)
                #get total P/L and multiply by the number of shares
                pl = float(position.unrealized_pl)
                #get current price
                current_price = latest_prices[symbol]
                self.positions[symbol] = {'shares': shares, 'buy_price': buy_price, 'current_price': current_price, 'pl': pl}


    def add_position(self, symbol, shares, buy_price):
        self.positions[symbol] = {'shares': shares, 'buy_price': buy_price, 'current_price': 0, 'pl': 0}
        self.update_positions()


    def remove_position(self, symbol):
        
        if symbol in self.positions:
            del self.positions[symbol]
            self.update_positions()

    def execute_trade(self, symbol, signal):
        self.check_rate_limit()

        if signal == 'buy':
            self.buy(symbol)
            print(f"Executing buy for {symbol}.")
        elif signal == 'sell':
            print(f"Executing sell for {symbol}.")
            self.sell(symbol)
        elif signal == 'short':
            print(f"Executing short for {symbol}.")
            self.short(symbol)
        elif signal == 'cover':
            print(f"Executing cover for {symbol}.")
            self.cover(symbol)
            
    def short(self, symbol):
        self.check_rate_limit()
        qty = round(self.calculate_buy_quantity(symbol, 0.06))  # 10% fraction to invest
        if qty > self.min_qty:
            if symbol not in self.positions:
                self.positions[symbol] = {'shares': 0, 'buy_price': 0.0, 'current_price': 0, 'pl': 0}

            total_cost = qty * self.get_latest_price(symbol)
            if total_cost > self.buying_power:
                print(f"Not enough buying power to buy {qty} shares of {symbol}. Skipping trade.")
                return            
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=round(qty, 6) if qty >= 1 else qty,
                side='sell',
                type='market',
                time_in_force='day'
            )

            while order.status != 'filled':
                order = self.api.get_order(order.id)

            self.positions[symbol]['shares'] -= qty
            self.update_positions()
            print(f"Shorted {qty} shares of {symbol} at {order.filled_avg_price}.")
            self.positions[symbol]['buy_price'] = float(order.filled_avg_price)

            # Update the buying power after the short
            self.buying_power += qty * self.positions[symbol]['buy_price']

    def cover(self, symbol, loss_threshold=0.95):
        self.check_rate_limit()
        qty = round(self.calculate_sell_quantity(symbol, 0.06))  # 10% fraction to sell

        if qty > self.min_qty:
            if symbol in self.positions and self.positions[symbol]['shares'] < 0:
                current_price = float(self.api.get_latest_trade(symbol).price)
                loss_ratio = current_price / self.positions[symbol]['buy_price']




                if loss_ratio <= loss_threshold:
                    order = self.api.submit_order(
                        symbol=symbol,
                        qty=round(qty, 6) if qty >= 1 else qty,
                        side='buy',
                        type='market',
                        time_in_force='day'
                    )

                    while order.status != 'filled':
                        order = self.api.get_order(order.id)
                        time.sleep(.5)

                    self.positions[symbol]['shares'] += qty
                    self.update_positions()
                    print(f"Covered {qty} shares of {symbol} at {current_price} for a loss of {loss_ratio}.")

                    if self.positions[symbol]['shares'] == 0:
                        self.positions[symbol]['buy_price'] = 0.0

                    # Update the buying power after the cover
                    self.buying_power -= qty * current_price

    min_qty = 1  # define the minimum order quantity suitable for fractional trading

    def buy(self, symbol):
            self.check_rate_limit()
            qty = self.calculate_buy_quantity(symbol, 0.06)  # 10% fraction to invest
            if qty > self.min_qty:
                if symbol not in self.positions:
                    self.positions[symbol] = {'shares': 0, 'buy_price': 0.0, 'current_price': 0, 'pl': 0}

                total_cost = qty * self.get_latest_price(symbol)
                if total_cost > self.buying_power:
                    print(f"Not enough buying power to buy {qty} shares of {symbol}. Skipping trade.")
                    return

                order = self.api.submit_order(
                    symbol=symbol,
                    qty=round(qty, 6) if qty >= 1 else qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )

                # Wait for the order to fill
                while order.status != 'filled':
                    order = self.api.get_order(order.id)
                    # print('Waiting for order fill...')
                    time.sleep(2)

                self.positions[symbol]['shares'] += qty
                self.update_positions()
                
                print(f"Bought {qty} shares of {symbol} at {order.filled_avg_price}.")
                self.positions[symbol]['buy_price'] = float(order.filled_avg_price)


                # Update the buying power after the purchase
                self.buying_power -= qty * self.positions[symbol]['buy_price']


    def sell(self, symbol, profit_threshold=1.05):
        self.check_rate_limit()
        qty = self.calculate_sell_quantity(symbol, 0.06)  # 10% fraction to sell

        if qty > self.min_qty:
            if symbol in self.positions and self.positions[symbol]['shares'] > 0:
                current_price = float(self.api.get_latest_trade(symbol).price)
                profit_ratio = current_price / self.positions[symbol]['buy_price']

                if profit_ratio >= profit_threshold:
                

                        order = self.api.submit_order(
                        symbol=symbol,
                        qty=round(qty, 6) if qty >= 1 else qty,
                        side='sell',
                        type='market',
                        time_in_force='day'
                    )

                # Wait for the order to fill
                while order.status != 'filled':
                    order = self.api.get_order(order.id)
                    time.sleep(.5)

                self.positions[symbol]['shares'] -= qty
                self.update_positions()
                print(f"Sold {qty} shares of {symbol} at {current_price} for a profit of {profit_ratio}.")

                if self.positions[symbol]['shares'] == 0:
                    self.positions[symbol]['buy_price'] = 0.0

                # Update the buying power after the sale
                self.buying_power += qty * current_price


    def get_buying_power(self):
        self.check_rate_limit()
        return float(self.api.get_account().buying_power)


    def get_latest_price(self, symbol):
        self.check_rate_limit()
        return float(self.api.get_latest_trade(symbol).price)

    def calculate_buy_quantity(self, symbol, fraction):
        self.check_rate_limit()
        """
        Calculate the quantity to buy for a symbol.

        Args:
        symbol (str): The symbol to calculate quantity for.
        fraction (float): The fraction of total equity to spend.

        Returns:
        float: The quantity to buy.
        """
        # Calculate total cost
        total_cost = self.buying_power * fraction
        #get the current price
        current_price = self.get_latest_price(symbol)
        
        # Calculate quantity based on total cost and current price
        qty = total_cost / current_price if current_price > 0 else 0

        # If total cost is less than 1, set quantity to 0
        if total_cost < 1:
            qty = 0

        return qty

    
    def calculate_sell_quantity(self, symbol, fraction):
        self.check_rate_limit()
        """
        Calculate the quantity to sell for a symbol.

        Args:
        symbol (str): The symbol to calculate quantity for.
        fraction (float): The fraction of total equity to sell.

        Returns:
        float: The quantity to sell.
        """
        # Calculate total cost
        total_cost = self.positions[symbol]['current_price'] * self.positions[symbol]['shares'] * fraction
        current_price = self.get_latest_price(symbol)
        
        # Calculate quantity based on total cost and current price
        qty = total_cost / current_price if current_price > 0 else 0

        # If total cost is less than 1, set quantity to 0
        if total_cost < 1:
            qty = 0

        return qty


    def get_market_regime_data(self, symbol, period):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period)

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

    
    def get_market_regime(self, symbol, short_period=10, long_period=20, adx_period=14, atr_period=14):
        self.check_rate_limit()
        
        market_data = self.get_market_regime_data(symbol, period=max(long_period+100, adx_period+100, atr_period+100))
        # market_data = market_data.fillna(0, inplace=True)
        # print(market_data)
        market_data['symbol'] = symbol
        market_data['short_sma'] = talib.SMA(market_data['close'], timeperiod=short_period)
        market_data['long_sma'] = talib.SMA(market_data['close'], timeperiod=long_period)
        market_data['adx'] = talib.ADX(market_data['high'], market_data['low'], market_data['close'], timeperiod=adx_period)
        market_data['atr'] = talib.ATR(market_data['high'], market_data['low'], market_data['close'], timeperiod=atr_period)

        market_data['sma_trend'] = np.where(market_data['short_sma'] > market_data['long_sma'], 1, np.where(market_data['short_sma'] < market_data['long_sma'], -1, 0))

        

        adx_threshold = 25
        atr_threshold = 1.5 * market_data['atr'].median()
        market_data['median_atr'] = market_data['atr'].median()

  

        #send market regime data for each symbol to a csv
        market_data.to_csv(f'./market_regime_data/{symbol}_market_regime.csv')
 

        if market_data['sma_trend'].iloc[-1] > 0 and market_data['adx'].iloc[-1] > adx_threshold:
            return 'bullish'
        elif market_data['sma_trend'].iloc[-1] < 0 and market_data['adx'].iloc[-1] > adx_threshold:
            return 'bearish'
        elif market_data['atr'].iloc[-1] < atr_threshold:
            return 'low_volatility'
        else:
            return 'high_volatility'



    def get_short_positions(self):
        self.check_rate_limit()
        short_positions = {}
        for symbol, position_data in self.positions.items():
            if position_data['shares'] < 0:
                short_positions[symbol] = position_data
        return short_positions










    # def adjust_parameters(self, symbol, volatility):
    #     volatility_score = (volatility['ATR'] + volatility['STDDEV']) / 2
    #     scaler = MinMaxScaler(feature_range=(14, 28))
    #     volatility_array = np.array(volatility_score).reshape(-1, 1)
    #     rsi_period = int(scaler.fit_transform(volatility_array)[0][0])

    #     return {'rsi_period': rsi_period}
    

    # def optimize_portfolio(self):
    #     # Get the current portfolio
    #     self.check_rate_limit()
    #     current_portfolio = self.api.list_positions()

    #     # Calculate the equal weight for each asset
    #     equal_weight = 1.0 / len(current_portfolio)

    #     # Adjust the portfolio to the target weights
    #     for position in current_portfolio:
    #         symbol = position.symbol
    #         target_quantity = equal_weight * self.api.get_account().cash
    #         self.api.submit_order(symbol, target_quantity, 'buy', 'limit', 'day')


    # def manage_risk(self):
    #     # Get the current portfolio
    #     self.check_rate_limit()

    #     current_portfolio = self.api.list_positions()

    #     # Set a market sell order for each asset
    #     for position in current_portfolio:
    #         symbol = position.symbol
    #         qty = float(position.qty)
    #         if qty > self.min_qty:
    #             self.api.submit_order(
    #                 symbol=symbol,
    #                 qty=qty,
    #                 side='sell',
    #                 type='market',
    #                 time_in_force='day'
    #             )