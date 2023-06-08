
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

def choose_base_models():
    base_models = [
        ('logistic_regression', LogisticRegression(random_state=42)),
        ('decision_tree', DecisionTreeClassifier(random_state=42)),
        ('svm', SVC(random_state=42)),
        ('random_forest', RandomForestClassifier(random_state=42)),
        ('knn', KNeighborsClassifier())
    ]
    return base_models
