# define a function to create labels
def create_labels(df, col_name):
    """Creates a label for the price difference."""
    # create a list to keep the labels
    labels = []
    # get the price differences
    diff = df[col_name].diff()
    for d in diff:
        if d > df[col_name].std():
            labels.append(2)  # 'price went up a lot'
        elif d > 0:
            labels.append(1)  # 'price went up a little'
        elif d == 0:
            labels.append(0)  # 'price stayed the same'
        elif d < -df[col_name].std():
            labels.append(-2)  # 'price went down a lot'
        else:
            labels.append(-1)  # 'price went down a little'
    return labels

# Load sklearn libraries
import datetime
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from datetime import timezone


from trading_signals import calculate_technical_indicators, get_tiingo_data

def train_model(symbols, start_date, end_date):
    # Create a dictionary to store models for each symbol
    models = {}

    for symbol in symbols:
        df = get_tiingo_data(symbol, start_date, end_date)

        df = calculate_technical_indicators(df)
        df.to_csv(f'./data-training/{symbol}_trading_data.csv')
        #drop symbol 
        df = df.drop(columns=['symbol'])
        df['labels'] = create_labels(df, 'close')

        # Define feature columns and target column
        features = df.drop(columns=['labels'])
        target = df['labels']

        # Split the data into train and test datasets
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

        # Create the classifier and fit it to our training data
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Use the fitted model to make predictions on the test data and evaluate the model
        y_pred = model.predict(X_test)
        print(classification_report(y_test, y_pred))
        print(confusion_matrix(y_test, y_pred))

        # Save the model into the models dictionary
        models[symbol] = model
        # Save the model to disk
        joblib.dump(model, f'./models/{symbol}_model.pkl')

    # Return the dictionary of trained models
    return models




from datetime import datetime, timedelta
import pandas as pd

import datetime
from dateutil.relativedelta import relativedelta

# Define the function to fetch the data
def fetch_stock_data(symbol, get_tiingo_data):
    # Define market hours in Eastern Time
    market_open_hour = 9
    market_open_minute = 30
    market_close_hour = 16
    market_close_minute = 0

    # Define the total minutes market is open each day
    market_minutes_per_day = (market_close_hour - market_open_hour) * 60 + (market_close_minute - market_open_minute)
    
    # Define the total rows to fetch each time
    rows_per_fetch = 10000

    # Define the total days needed per fetch considering market hours
    days_per_fetch = rows_per_fetch // market_minutes_per_day
    
    # Define the end date as today's date
    end_date = datetime.datetime.now()
    
    # Define the start date as 5 years ago
    start_date = end_date - relativedelta(days=1825)
    
    # Loop over the days to fetch the data
    while start_date < end_date:
        next_end_date = start_date + relativedelta(days=days_per_fetch)
        
        # If next_end_date is in the future, set it as end_date
        if next_end_date > end_date:
            next_end_date = end_date

        # Fetch the data for this interval
        df = get_tiingo_data(symbol, start_date, next_end_date)
        df.to_csv(f'./data-training/{symbol}_training_data.csv')

        # TODO: process the dataframe as needed...

        # Update the start_date for the next iteration
        start_date = next_end_date

    

# Call the function
fetch_stock_data('AAPL', get_tiingo_data)  # Uncomment this line if you want to run the function

# symbols = ['CNX', 'CPB', 'EPAM', 'SPY']
# start_date = datetime.datetime(2021, 1, 1)
# end_date = datetime.datetime(2023, 6, 1)

# for symbol in symbols:

#     df = get_total_data(symbol, start_date, end_date)
#     df.to_csv(f'./data-training/{symbol}_trading_data.csv')


# models = train_model(symbols, start_date, end_date)
