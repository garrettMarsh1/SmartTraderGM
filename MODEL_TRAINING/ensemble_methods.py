
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score
from sklearn.base import clone

def bagging_model(X_train, y_train, X_test, y_test):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy

def boosting_model(X_train, y_train, X_test, y_test):
    model = AdaBoostClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy

def gradient_boosting_model(X_train, y_train, X_test, y_test):
    model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy

def stacking_model(base_models, final_model, X_train, y_train, X_test, y_test):
    # Train base models
    for model in base_models:
        model.fit(X_train, y_train)
    
    # Generate predictions for the final model
    final_model_input = np.column_stack([model.predict(X_test) for model in base_models])
    
    # Train the final model
    final_model.fit(final_model_input, y_test)
    
    # Generate predictions
    y_pred = final_model.predict(final_model_input)
    accuracy = accuracy_score(y_test, y_pred)
    return final_model, accuracy

def ensemble_method(base_models, final_model, X_train, y_train, X_test, y_test):
    # Train base models and get their accuracies
    base_model_accuracies = []
    for model in base_models:
        model_clone = clone(model)
        model_clone.fit(X_train, y_train)
        y_pred = model_clone.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        base_model_accuracies.append(accuracy)
    
    # Train the ensemble model
    ensemble_model, ensemble_accuracy = stacking_model(base_models, final_model, X_train, y_train, X_test, y_test)
    
    return base_model_accuracies, ensemble_accuracy
