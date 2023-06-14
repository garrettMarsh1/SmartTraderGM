import datetime
import os
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from portfolio import Portfolio
from trading_signals import get_tiingo_data, calculate_technical_indicators, generate_trading_signals

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize API keys and credentials
alpaca_api_key = os.getenv("APCA_API_KEY")
alpaca_secret_key = os.getenv("APCA_API_SECRET")
alpaca_base_url = "https://paper-api.alpaca.markets"

# Initialize portfolio
portfolio = Portfolio(alpaca_api_key, alpaca_secret_key, alpaca_base_url)

# Initialize symbols
symbols_list = ['CG', 'ARES', 'BX', 'ALC', 'BSTZ', 'COLD', 'ET', 'FLEX', 'MX', 'MRK', 
               'GE', 'LIN', 'LMT', 'NOC', 'RTX', 'TSLA', 'WMT', 'ZM', 'NVDA', 'MSFT', 
               'AAPL', 'GOOGL']

@app.route('/symbols', methods=['GET', 'POST'])
def handle_symbols():
    global symbols_list
    if request.method == 'GET':
        return jsonify(symbols_list)
    elif request.method == 'POST':
        data = request.get_json()
        symbols_list = data.get('symbols', symbols_list)
        return jsonify(symbols_list), 200

@app.route('/portfolio/positions', methods=['GET'])
def get_positions():
    portfolio.update_positions()
    return jsonify(portfolio.positions)

@app.route('/portfolio/position', methods=['POST'])
def add_position():
    data = request.get_json()
    portfolio.add_position(data['symbol'], data['shares'], data['buy_price'])
    return jsonify(portfolio.positions)

@app.route('/portfolio/position', methods=['DELETE'])
def remove_position():
    for symbol in portfolio.positions:
        portfolio.remove_position(symbol)

@app.route('/portfolio/trade', methods=['POST'])
def execute_trade():
    data = request.get_json()
    portfolio.execute_trade(data['symbol'], data['signal'])
    return jsonify(portfolio.positions)

@app.route('/portfolio/buy', methods=['POST'])
def buy():
    symbol = request.args.get('symbol')
    portfolio.buy(symbol)
    return jsonify(portfolio.positions)

@app.route('/portfolio/sell', methods=['POST'])
def sell():
    symbol = request.args.get('symbol')
    portfolio.sell(symbol)
    return jsonify(portfolio.positions)

@app.route("/portfolio/update_positions", methods=['POST'])
def update_positions():
    portfolio.update_positions()
    return {"status": "positions updated"}

@app.route("/portfolio/get_total_value", methods=['GET'])
def get_total_value():
    return {"total_value": portfolio.get_total_value()}

@app.route("/portfolio/get_cash", methods=['GET'])
def get_buying_power():
    return {"cash": portfolio.get_buying_power()}

@app.route("/portfolio/get_history/<symbol>", methods=['GET'])
def get_history(symbol: str):
    return {"history": portfolio.get_history(symbol)}

@app.route("/portfolio/get_asset_info/<symbol>", methods=['GET'])
def get_asset_info(symbol: str):
    return portfolio.get_asset_info(symbol)

@app.route('/market_data', methods=['GET'])
def execute_trades_by_signal():
    global symbols_list
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=1)

    # Fetch data from Tiingo
    df = get_tiingo_data(symbols_list, start_date, end_date)

    # Calculate technical indicators
    df_indicators = calculate_technical_indicators(df)

    # Generate trading signals
    signals = generate_trading_signals(df_indicators, portfolio)

    return jsonify(signals)

# define market data fetching and sending over websocket

def fetch_and_send_market_data():
    global symbols_list
    while True:
        for symbol in symbols_list:
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=1)

            # Fetch data from Tiingo
            df = get_tiingo_data(symbol, start_date, end_date)

            # Calculate technical indicators
            df_indicators = calculate_technical_indicators(df)


            data = {
                "symbol": symbol,  # adding symbol to the data
                "data": df_indicators.to_json(),
                "positions": portfolio.positions,
                
            }
            
            # Send the data to the client over WebSocket
            socketio.emit('market_data', data)

            # wait for a certain period of time (for example, 1 second) before fetching the data again
            time.sleep(5)

# start a new thread that constantly fetches and sends market data
threading.Thread(target=fetch_and_send_market_data).start()

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)
