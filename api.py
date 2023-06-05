import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from portfolio import Portfolio
from trading_signals import get_tiingo_data


app = Flask(__name__)
CORS(app)

# Initialize API keys and credentials
alpaca_api_key = os.getenv("APCA_API_KEY")
alpaca_secret_key = os.getenv("APCA_API_SECRET")
alpaca_base_url = "https://paper-api.alpaca.markets"

# Initialize portfolio
portfolio = Portfolio(alpaca_api_key, alpaca_secret_key, alpaca_base_url)


@app.route('/api/portfolio', methods=['GET'])
def get_positions():
    portfolio.update_positions()
    return jsonify(portfolio.positions)

@app.route('/api/portfolio/<string:symbol>', methods=['POST'])
def add_position(symbol):
    shares = request.json.get('shares')
    buy_price = request.json.get('buy_price')
    portfolio.add_position(symbol, shares, buy_price)
    return jsonify(portfolio.positions)

@app.route('/api/portfolio/<string:symbol>', methods=['DELETE'])
def remove_position(symbol):
    portfolio.remove_position(symbol)
    return jsonify(portfolio.positions)

@app.route('/api/portfolio/<string:symbol>/market-regime', methods=['GET'])
def get_market_regime(symbol):
    market_regime = portfolio.get_market_regime(symbol)
    return jsonify({'market_regime': market_regime})

@app.route('/api/portfolio/<string:symbol>/market-data', methods=['GET'])
def get_market_data(symbol, start_date, end_date):
    market_data = get_tiingo_data(symbol, start_date, end_date)
    return jsonify({'market_data': market_data})

if __name__ == '__main__':
    app.run(debug=True)
    