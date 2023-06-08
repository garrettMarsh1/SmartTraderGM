
import pandas as pd
import numpy as np
import joblib
from trading_signals import get_tiingo_data, calculate_technical_indicators

def make_predictions(symbol, start_date, end_date, model_path):
    # Load the trained ensemble model
    ensemble_model = joblib.load(model_path)

    # Get stock data and calculate technical indicators
    stock_data = get_tiingo_data(symbol, start_date, end_date)
    stock_data = calculate_technical_indicators(stock_data)

    # Prepare data for prediction
    X = stock_data.drop(columns=['symbol']).values

    # Make predictions using the ensemble model
    predictions = ensemble_model.predict(X)

    # Add predictions to the stock data DataFrame
    stock_data['predictions'] = predictions

    return stock_data

# Example usage
if __name__ == "__main__":
    symbol = "AAPL"
    start_date = "2021-01-01"
    end_date = "2021-12-31"
    model_path = "trained_ensemble_model.pkl"

    predictions_df = make_predictions(symbol, start_date, end_date, model_path)
    print(predictions_df)

