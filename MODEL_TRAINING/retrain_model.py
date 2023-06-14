
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from train_ensemble_model import ensemble_model
from train_test_split import X_train, X_test, y_train, y_test

def retrain_model(model, X_train, y_train, X_test, y_test, new_params):
    model.set_params(**new_params)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    return model, accuracy, report

# Example usage:
# new_params = {'n_estimators': 100, 'max_depth': 10}
# retrained_model, new_accuracy, new_report = retrain_model(ensemble_model, X_train, y_train, X_test, y_test, new_params)
# print("New Accuracy:", new_accuracy)
# print("New Classification Report:\n", new_report)

