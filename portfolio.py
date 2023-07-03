import datetime
from datetime import timedelta, datetime
import math
import time
import alpaca_trade_api as tradeapi
import asyncio


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

                current_price = latest_prices[symbol]
                self.positions[symbol] = {'shares': shares, 'buy_price': buy_price, 'current_price': current_price, 'pl': pl}


    def add_position(self, symbol, shares, buy_price):
        self.positions[symbol] = {'shares': shares, 'buy_price': buy_price, 'current_price': 0, 'pl': 0}
        self.update_positions()


    def remove_position(self, symbol):
        
        if symbol in self.positions:
            del self.positions[symbol]
            self.update_positions()

    async def execute_trade(self, symbol, signal, retries=3):
        self.check_rate_limit()
        # print(f'Symbol: {symbol}, Signal: {signal}')

        for i in range(retries):
            try:
                if signal == 'buy':
                    await self.buy(symbol)
                    print(f"Executing buy for {symbol}.")
                    await asyncio.sleep(1.5)
                elif signal == 'sell':
                    #no shares to sell check
                    if symbol not in self.positions:
                        print(f"No shares of {symbol} to sell. Skipping trade.")
                        return
                    else:
                        print(f"Executing sell for {symbol}.")
                        await self.sell(symbol)
                        await asyncio.sleep(1.5)
                elif signal == 'short':
                    #buying power check before short
                    print(f"Executing short for {symbol}.")
                    print(self.buying_power)
                    if self.buying_power < 0:
                        print(f"Not enough buying power to short {symbol}. Skipping trade.")
                        return
                    else:
                        print(f"Executing short for {symbol}.")
                        await self.short(symbol)
                        await asyncio.sleep(1.5)

                elif signal == 'cover':
                    print(f"Executing cover for {symbol}.")
                    await self.cover(symbol)
                    await asyncio.sleep(1.5)
                
                # If the code reaches this point, then the order was executed successfully.
                # So, break the loop.
                break

            except Exception as e:
                if i < retries - 1:  # i is zero indexed
                    await asyncio.sleep(2)  # Wait for 2 seconds before retrying
                    continue
                else:
                    # If this is the final attempt and it still failed, re-raise the exception.
                    print(f"Order failed after {retries} attempts.")
                    raise e
                    
    async def short(self, symbol, stop_loss_percentage=0.05, take_profit_percentage=0.10):
        self.check_rate_limit()
        qty = math.floor(self.calculate_buy_quantity(symbol, 0.06))  # 10% fraction to invest
        if qty > self.min_qty:
            total_cost = qty * self.get_latest_price(symbol)
            if total_cost > self.buying_power:
                print(f"Not enough buying power to buy {qty} shares of {symbol}. Skipping trade.")
                return            

            current_price = self.get_latest_price(symbol)
            stop_loss_price = round(current_price * (1 + stop_loss_percentage), 2)
            take_profit_price = round(current_price * (1 - take_profit_percentage), 2)

            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='market',
                time_in_force='gtc',
                order_class='bracket',
                take_profit={'limit_price': take_profit_price},
                stop_loss={'stop_price': stop_loss_price}
            )

            while order.status != 'filled':
                order = self.api.get_order(order.id)
                await asyncio.sleep(1)  # Non-blocking sleep

            print(f"Shorted {qty} shares of {symbol} at {order.filled_avg_price}.")
            self.update_positions()
            self.buying_power -= qty * float(order.filled_avg_price)





    async def cover(self, symbol):
        self.check_rate_limit()
        qty = math.floor(self.calculate_buy_quantity(symbol, 0.06))  

        if qty > self.min_qty:
            if symbol in self.positions and self.positions[symbol]['shares'] < 0:
                current_price = float(self.api.get_latest_trade(symbol).price)
                current_price = self.get_latest_price(symbol)

                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )

                while order.status != 'filled':
                    order = self.api.get_order(order.id)
                    await asyncio.sleep(0.5)  # Non-blocking sleep

                self.positions[symbol]['shares'] += qty
                self.update_positions()
                

                if self.positions[symbol]['shares'] == 0:
                    self.positions[symbol]['buy_price'] = 0.0

                self.buying_power += qty * float(current_price)



    min_qty = 1  # define the minimum order quantity suitable for fractional trading

    async def buy(self, symbol, stop_loss_percentage=0.05, take_profit_percentage=0.10):
        self.check_rate_limit()
        qty = math.floor(self.calculate_buy_quantity(symbol, 0.06))
        current_price = self.get_latest_price(symbol)
        limit_price = round(current_price * 1.001, 2)
        stop_loss_price = round(current_price * (1 - stop_loss_percentage), 2)
        take_profit_price = round(current_price * (1 + take_profit_percentage), 2)
        print(f'Buying {qty} share(s) of {symbol}')  

        if qty > self.min_qty:
            if symbol not in self.positions:
                self.positions[symbol] = {'shares': 0, 'buy_price': 0.0, 'current_price': 0, 'pl': 0}

            total_cost = qty * limit_price  # The limit price replaces the last price here
            if total_cost > self.buying_power:
                print(f"Not enough buying power to buy {qty} shares of {symbol}. Skipping trade.")
                return
                

            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='limit',  # Change order type to 'limit'
                limit_price=limit_price,  # Add limit price
                time_in_force='gtc',
                order_class='bracket',
                take_profit={'limit_price': take_profit_price},
                stop_loss={'stop_price': stop_loss_price}
            )

            while order.status != 'filled':
                order = self.api.get_order(order.id)
                await asyncio.sleep(2)  # Non-blocking sleep

            self.positions[symbol]['shares'] += qty
            self.update_positions()

            print(f"Bought {qty} shares of {symbol} at {order.filled_avg_price}.")
            self.positions[symbol]['buy_price'] = float(order.filled_avg_price)

            self.buying_power -= qty * float(self.positions[symbol]['buy_price'])




    async def sell(self, symbol, stop_loss_percentage=0.05, take_profit_percentage=0.10):
        self.check_rate_limit()
        qty = math.floor(self.calculate_sell_quantity(symbol, 0.06))  # 10% fraction to sell
        print(f"Trying to sell {qty} shares of {symbol}.")
        if qty > self.min_qty:
            if symbol in self.positions and self.positions[symbol]['shares'] > 0:
                current_price = float(self.api.get_latest_trade(symbol).price)
                profit_ratio = current_price / self.positions[symbol]['buy_price']
                
                current_price = self.get_latest_price(symbol)
                limit_price = current_price * 1.001  # set limit price as 0.1% above the current price
                stop_loss_price = round(current_price * (1 + stop_loss_percentage), 2)
                take_profit_price = round(current_price * (1 - take_profit_percentage), 2)
        
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side='buy',
                    type='limit',
                    limit_price=limit_price,
                    time_in_force='gtc',
                    order_class='bracket',
                    take_profit={'limit_price': take_profit_price},
                    stop_loss={'stop_price': stop_loss_price}
                )

            while order.status != 'filled':
                order = self.api.get_order(order.id)
                await asyncio.sleep(0.5)  # Non-blocking sleep

            self.positions[symbol]['shares'] -= qty
            self.update_positions()
            print(f"Sold {qty} shares of {symbol} at {current_price} for a profit of {profit_ratio}.")

            if self.positions[symbol]['shares'] == 0:
                self.positions[symbol]['buy_price'] = 0.0

            self.buying_power += qty * float(current_price)



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






    def get_short_positions(self):
        self.check_rate_limit()
        short_positions = {}
        for symbol, position_data in self.positions.items():
            if position_data['shares'] < 0:
                short_positions[symbol] = position_data
        return short_positions

    
    # def optimize_portfolio(self):
    #     # Get the current portfolio
    #     self.check_rate_limit()
    #     current_portfolio = self.api.list_positions()

    #     # Calculate the equal weight for each asset
    #     equal_weight = 1.0 / len(current_portfolio)

    #     # Adjust the portfolio to the target weights
    #     for position in current_portfolio:
    #         symbol = position.symbol
    #         # Get the current price of the stock
    #         current_price = self.api.get_latest_trade(symbol).price
    #         # Calculate the target quantity
    #         target_quantity = int((equal_weight * float(self.api.get_account().buying_power)) / current_price)
    #         print(target_quantity)
    #         # Check if target_quantity is greater than 0 before submitting the order
    #         if target_quantity > 0:
    #             # Submit the order with a limit price (here, the current price is used as the limit price)
    #             self.api.submit_order(symbol, target_quantity, 'buy', 'limit', 'day', limit_price=current_price)
    #         else:
    #             print(f"Insufficient buying power to purchase {symbol}, or target quantity is 0.")
    



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