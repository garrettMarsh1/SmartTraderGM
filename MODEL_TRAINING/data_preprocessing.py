
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from trading_signals import get_tiingo_data, calculate_technical_indicators

def preprocess_data(symbol, start_date, end_date):
    # Get data and calculate technical indicators
    raw_data = get_tiingo_data(symbol, start_date, end_date)
    data_with_indicators = calculate_technical_indicators(raw_data)

    # Drop unnecessary columns
    data_with_indicators.drop(columns=['open', 'volume', 'symbol'], inplace=True)

    # Scale the features
    scaler = MinMaxScaler()
    scaled_data = pd.DataFrame(scaler.fit_transform(data_with_indicators), columns=data_with_indicators.columns, index=data_with_indicators.index)

    return scaled_data


