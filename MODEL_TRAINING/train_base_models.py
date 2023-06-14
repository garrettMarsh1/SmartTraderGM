
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from data_preprocessing import preprocess_data
from train_test_split import split_data

def train_base_models(X_train, y_train):
    # Initialize base models
    lr = LogisticRegression(random_state=42)
    dt = DecisionTreeClassifier(random_state=42)
    svm = SVC(random_state=42)

    # Train base models
    lr.fit(X_train, y_train)
    dt.fit(X_train, y_train)
    svm.fit(X_train, y_train)

    return lr, dt, svm

if __name__ == "__main__":
    # Load and preprocess data
    df = pd.read_csv("historical_data.csv")
    df = preprocess_data(df)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = split_data(df)

    # Train base models
    lr, dt, svm = train_base_models(X_train, y_train)

    # Save trained models
    with open("trained_base_models.pkl", "wb") as f:
        pickle.dump((lr, dt, svm), f)

