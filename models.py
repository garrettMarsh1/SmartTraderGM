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
        df.fillna(0, inplace=True)

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




    

# Call the function
# fetch_stock_data('AAPL', get_tiingo_data)  # Uncomment this line if you want to run the function

symbols = ['BP', 'NTR', 'CTRA', 'KMI', 'CNX', 'NFG', 'ZG']
start_date = datetime.datetime(2021, 1, 1)
end_date = datetime.datetime(2023, 6, 1)

for symbol in symbols:
    models = train_model(symbols, start_date, end_date)
