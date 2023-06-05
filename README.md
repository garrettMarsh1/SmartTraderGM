# SmartTraderGM

This project is a Python-based algorithmic trading bot capable of executing buy and sell orders for ETFs and stocks on the Alpaca Paper Market. The bot implements robust and well-founded trading strategies, ensuring optimal risk management and consistent profitability.

## Installation

1. Clone the repository:

```
git clone 
cd algorithmic-trading-bot
```

2. Create a virtual environment and activate it:

```
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:

```
TO INSTALL TA-LIB VISIT THIS LINK AND DOWNLOAD THE WHEEL FILE ASSOCIATED WITH YOUR PYTHON VERSION. CURRENTLY I AM RUNNING VERSION 3.10.9
ONCE THE WHEEL IS INSTALLED, PLACE IT IN THIS DIRECTORY BEFORE INSTALLING REQUIREMENTS. 
https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install -r requirements.txt
```

4. Set up your API keys as environment variables:

```
It is reccomended to save your api keys as environment variables. 

TIINGO_API_KEY=os.environ.get("your_api_key")
ALPACA_API_KEY=os.environ.get("your_api_key")
ALPACA_SECRET_KEY=os.environ.get("your_api_key")
ALPACA_BASE_URL="https://paper-api.alpaca.markets"
```

## Usage

1. Run the main.py file to start the trading bot:

```
python main.py
```

2. Monitor the bot's performance and adjust the trading strategy as needed.


## Contributing

Feel free to submit pull requests or open issues to improve the trading bot. Please follow best practices in Python programming and algorithmic trading, and ensure that you document your code and follow a consistent style guide for better readability and maintainability.
