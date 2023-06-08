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
            #get current profit/loss percentage from


            for position in positions:
                symbol = position.symbol
                shares = float(position.qty)
                buy_price = float(position.avg_entry_price)
                #get total P/L and multiply by the number of shares
                pl = float(position.unrealized_pl)
                percentage_profit = (abs(pl) / (abs(shares) * abs(buy_price))) * 100  # calculate profit percentage using absolute values

                current_price = latest_prices[symbol]
                self.positions[symbol] = {'shares': shares, 'buy_price': buy_price, 'current_price': current_price, 'pl': pl, 'percentage_profit': percentage_profit}


    def add_position(self, symbol, shares, buy_price):
        self.positions[symbol] = {'shares': shares, 'buy_price': buy_price, 'current_price': 0, 'pl': 0}
        self.update_positions()


    def remove_position(self, symbol):
        
        if symbol in self.positions:
            del self.positions[symbol]
            self.update_positions()

    def execute_trade(self, symbol, signal):
        self.check_rate_limit()
        print(f'Symbol: {symbol}, Signal: {signal}')
        # print(f"Executing trade for {symbol}.")

        if signal == 'buy':
            self.buy(symbol)
            print(f"Executing buy for {symbol}.")
        elif signal == 'sell':
            #no shares to sell check
            if symbol not in self.positions:
                print(f"No shares of {symbol} to sell. Skipping trade.")
                return
            else:
                print(f"Executing sell for {symbol}.")
                self.sell(symbol)
        elif signal == 'short':
            #buying power check before short
            print(f"Executing short for {symbol}.")
            print(self.buying_power)
            if self.buying_power < 0:
                print(f"Not enough buying power to short {symbol}. Skipping trade.")
                return
            else:
                print(f"Executing short for {symbol}.")
                self.short(symbol)

        elif signal == 'cover':
            print(f"Executing cover for {symbol}.")
            self.cover(symbol)
            
    def short(self, symbol):
        self.check_rate_limit()
        qty = round(self.calculate_buy_quantity(symbol, 0.06))  # 10% fraction to invest
        print(qty)
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
            # Update the buying power after the short
            self.buying_power -= qty * self.positions[symbol]['buy_price']


    def cover(self, symbol, profit_threshold=4.0):
        self.check_rate_limit()
        qty = round(self.calculate_sell_quantity(symbol, 0.06))  # 10% fraction to sell

        if qty > self.min_qty:
            if symbol in self.positions and self.positions[symbol]['shares'] < 0:
                current_price = float(self.api.get_latest_trade(symbol).price)
                percentage_profit = self.positions[symbol]['percentage_profit']
                
                if percentage_profit >= profit_threshold:
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
                    print(f"Covered {qty} shares of {symbol} at {current_price} with a profit percentage of {percentage_profit}%.")

                    if self.positions[symbol]['shares'] == 0:
                        self.positions[symbol]['buy_price'] = 0.0

                    # Update the buying power after the cover
                    self.buying_power += qty * current_price


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
            
        required_period = max(long_period+1000, adx_period+1000, atr_period+1000)
        market_data = self.get_market_regime_data(symbol, period=required_period)
        market_data['symbol'] = symbol

        close = market_data['close']
        high = market_data['high']
        low = market_data['low']

        short_sma = talib.SMA(close, timeperiod=short_period)
        long_sma = talib.SMA(close, timeperiod=long_period)
        adx = talib.ADX(high, low, close, timeperiod=adx_period)
        atr = talib.ATR(high, low, close, timeperiod=atr_period)

        sma_trend = (short_sma > long_sma).astype(int) - (short_sma < long_sma).astype(int)

        market_data = market_data.assign(
            short_sma=short_sma,
            long_sma=long_sma,
            adx=adx,
            atr=atr,
            sma_trend=sma_trend,
        )

        atr_threshold = 1.5 * atr.median()
        market_data['median_atr'] = atr.median()

        market_data.to_csv(f'./market_regime_data/{symbol}_market_regime.csv')
        #fill with 0s
        market_data = market_data.fillna(0)

        last_sma_trend = sma_trend.iat[-1]
        last_adx = adx.iat[-1]
        last_atr = atr.iat[-1]

        if last_sma_trend > 0 and last_adx > 25:
            return 'bullish'
        elif last_sma_trend < 0 and last_adx > 25:
            return 'bearish'
        elif last_atr < atr_threshold:
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

    
    def optimize_portfolio(self):
        # Get the current portfolio
        self.check_rate_limit()
        current_portfolio = self.api.list_positions()

        # Calculate the equal weight for each asset
        equal_weight = 1.0 / len(current_portfolio)

        # Adjust the portfolio to the target weights
        for position in current_portfolio:
            symbol = position.symbol
            # Get the current price of the stock
            current_price = self.api.get_latest_trade(symbol).price
            # Calculate the target quantity
            target_quantity = int((equal_weight * float(self.api.get_account().buying_power)) / current_price)
            print(target_quantity)
            # Check if target_quantity is greater than 0 before submitting the order
            if target_quantity > 0:
                # Submit the order with a limit price (here, the current price is used as the limit price)
                self.api.submit_order(symbol, target_quantity, 'buy', 'limit', 'day', limit_price=current_price)
            else:
                print(f"Insufficient buying power to purchase {symbol}, or target quantity is 0.")
    



    def manage_risk(self):
        # Get the current portfolio
        self.check_rate_limit()

        current_portfolio = self.api.list_positions()

        # Set a market sell order for each asset
        for position in current_portfolio:
            symbol = position.symbol
            qty = float(position.qty)
            if qty > self.min_qty:
                self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='sell',
                    type='market',
                    time_in_force='day'
                )