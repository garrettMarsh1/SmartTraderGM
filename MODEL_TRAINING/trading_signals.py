
import pandas as pd
from data_preprocessing import preprocess_data
from train_test_split import split_data
from base_models import choose_base_models
from train_base_models import train_base_models
from ensemble_methods import choose_ensemble_method
from train_ensemble_model import train_ensemble_model
from evaluate_model import evaluate_model
from retrain_model import retrain_model
from make_predictions import make_predictions

# Load and preprocess data
symbol = "AAPL"
start_date = "2020-01-01"
end_date = "2020-12-31"
raw_data = get_tiingo_data(symbol, start_date, end_date)
technical_indicators = calculate_technical_indicators(raw_data)
preprocessed_data = preprocess_data(technical_indicators)

# Split data into training and testing sets
train_data, test_data = split_data(preprocessed_data)

# Choose and train base models
base_models = choose_base_models()
trained_base_models = train_base_models(base_models, train_data)

# Choose ensemble method and train ensemble model
ensemble_method = choose_ensemble_method()
ensemble_model = train_ensemble_model(ensemble_method, trained_base_models, train_data)

# Evaluate model performance
performance_metrics = evaluate_model(ensemble_model, test_data)

# Retrain model if necessary
while not satisfactory_performance(performance_metrics):
    ensemble_model = retrain_model(ensemble_model, train_data)
    performance_metrics = evaluate_model(ensemble_model, test_data)

# Make predictions on new data
predictions = make_predictions(ensemble_model, new_data)
