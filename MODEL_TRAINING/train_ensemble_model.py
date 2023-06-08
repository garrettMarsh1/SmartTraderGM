
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, classification_report
from data_preprocessing import preprocess_data
from train_test_split import split_data
from base_models import get_base_models

def train_ensemble_model(df, target_col):
    # Preprocess data
    df = preprocess_data(df)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = split_data(df, target_col)

    # Get base models
    base_models = get_base_models()

    # Train base models
    for name, model in base_models:
        model.fit(X_train, y_train)

    # Ensemble method: Voting Classifier
    ensemble_model = VotingClassifier(estimators=base_models, voting='soft')

    # Train ensemble model
    ensemble_model.fit(X_train, y_train)

    # Make predictions on test data
    y_pred = ensemble_model.predict(X_test)

    # Evaluate model
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print("Ensemble Model Accuracy:", accuracy)
    print("Classification Report:\n", report)

    return ensemble_model

if __name__ == "__main__":
    # Load processed data
    df = pd.read_csv("processed_data.csv")

    # Define target column
    target_col = "signal"

    # Train ensemble model
    ensemble_model = train_ensemble_model(df, target_col)

