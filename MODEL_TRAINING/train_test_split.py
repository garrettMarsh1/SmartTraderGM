
import pandas as pd
from sklearn.model_selection import train_test_split
from trading_signals import get_tiingo_data, calculate_technical_indicators

# Define your trading strategy to generate the target variable (buy, sell, short, cover, hold)
def generate_target_variable(df):
    # Example: Simple Moving Average Crossover Strategy
    df['signal'] = 0
    df.loc[df['sma_50'] > df['sma_200'], 'signal'] = 1
    df.loc[df['sma_50'] < df['sma_200'], 'signal'] = -1
    return df

# Load and preprocess data
symbol = "AAPL"
start_date = "2020-01-01"
end_date = "2020-12-31"
raw_data = get_tiingo_data(symbol, start_date, end_date)
data = calculate_technical_indicators(raw_data)
data = generate_target_variable(data)

# Split the data into training and testing datasets
X = data.drop(columns=['signal', 'symbol'])
y = data['signal']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

