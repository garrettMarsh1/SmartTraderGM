
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from train_ensemble_model import ensemble_model
from train_test_split import X_test, y_test

def evaluate_model():
    # Make predictions on the test data
    y_pred = ensemble_model.predict(X_test)

    # Calculate the accuracy of the model
    accuracy = accuracy_score(y_test, y_pred)

    # Print the accuracy
    print(f"Accuracy: {accuracy:.2f}")

    # Calculate the confusion matrix
    cm = confusion_matrix(y_test, y_pred)

    # Print the confusion matrix
    print("Confusion Matrix:")
    print(cm)

    # Calculate the classification report
    cr = classification_report(y_test, y_pred)

    # Print the classification report
    print("Classification Report:")
    print(cr)

if __name__ == "__main__":
    evaluate_model()

