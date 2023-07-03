from alpaca_trade_api import REST
import os
alpaca_api_key = os.getenv("APCA_API_KEY")
alpaca_secret_key = os.getenv("APCA_API_SECRET")
alpaca_base_url = "https://paper-api.alpaca.markets"

api = REST(alpaca_api_key, alpaca_secret_key, alpaca_base_url)

symbol = 'NVDA'
open_orders = api.list_orders(status='open', symbols=[symbol])

for order in open_orders:
    # Find the take_profit order
    if order.order_class == 'bracket' and order.type == 'limit':
        # Calculate the new take_profit price based on the 50% target
        new_take_profit_price = float(order.limit_price) * 1.5
        #round the new_take_profit_price to nearest whole number
        new_take_profit_price = round(new_take_profit_price)

        # Update the take_profit order
        api.replace_order(order.id, qty=order.qty, time_in_force=order.time_in_force,
                          limit_price=new_take_profit_price, stop_price=order.stop_price)

