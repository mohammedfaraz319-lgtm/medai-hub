"""Explainable risk models for diabetes and heart disease.

Logistic regression models trained on a synthetic population whose risk follows
published *direction-of-effect* relationships (age, BMI, glucose, BP, ...).
Because the model is linear, every prediction can be explained by listing which
inputs pushed the risk up the most.

To use real data, replace `generate_*` with a loader for the Pima Indians
Diabetes / UCI Heart Disease CSV files and call `train_all()` (see README).
"""
import json
import os

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(os.path.dirname(HERE), "models")

SPECS = {
    "diabetes": {
        "features": ["age", "bmi", "glucose", "systolic_bp", "family_history", "activity_days"],
        "labels": {
            "age": "Age", "bmi": "Body-mass index", "glucose": "Fasting glucose",
            "systolic_bp": "Systolic blood pressure", "family_history": "Family history of diabetes",
            "activity_days": "Physical activity (days/week)",
        },
        "ranges": {"age": (10, 100), "bmi": (12, 60), "glucose": (50, 400), "systolic_bp": (80, 220),
                   "family_history": (0, 1), "activity_days": (0, 7)},
    },
    "heart": {
        "features": ["age", "male", "systolic_bp", "cholesterol", "smoker", "diabetic", "bmi", "activity_days", "family_history"],
        "labels": {
            "age": "Age", "male": "Male sex", "systolic_bp": "Systolic blood pressure",
            "cholesterol": "Total cholesterol", "smoker": "Smoking", "diabetic": "Diabetes",
            "bmi": "Body-mass index", "activity_days": "Physical activity (days/week)",
            "family_history": "Family history of heart disease",
        },
        "ranges": {"age": (10, 100), "male": (0, 1), "systolic_bp": (80, 220), "cholesterol": (80, 500),
                   "smoker": (0, 1), "diabetic": (0, 1), "bmi": (12, 60), "activity_days": (0, 7),
                   "family_history": (0, 1)},
    },
}


def _sigmoid(z):
    return 1 / (1 + np.exp(-z))


def generate_diabetes(n=8000, seed=1):
    r = np.random.default_rng(seed)
    age = r.uniform(18, 80, n)
    bmi = np.clip(r.normal(27, 5, n), 15, 50)
    glucose = np.clip(r.normal(100, 25, n), 65, 300)
    sbp = np.clip(r.normal(125, 15, n), 90, 200)
    fam = (r.random(n) < .3).astype(float)
    act = r.integers(0, 8, n).astype(float)
    z = -11.0 + .025 * age + .09 * bmi + .045 * glucose + .01 * sbp + .7 * fam - .12 * act + r.normal(0, .3, n)
    y = (r.random(n) < _sigmoid(z)).astype(int)
    return np.column_stack([age, bmi, glucose, sbp, fam, act]), y


def generate_heart(n=8000, seed=2):
    r = np.random.default_rng(seed)
    age = r.uniform(25, 85, n)
    male = (r.random(n) < .5).astype(float)
    sbp = np.clip(r.normal(128, 17, n), 90, 210)
    chol = np.clip(r.normal(200, 40, n), 110, 400)
    smoker = (r.random(n) < .22).astype(float)
    diabetic = (r.random(n) < .12).astype(float)
    bmi = np.clip(r.normal(27, 5, n), 15, 50)
    act = r.integers(0, 8, n).astype(float)
    fam = (r.random(n) < .25).astype(float)
    z = (-9.5 + .06 * age + .5 * male + .02 * sbp + .004 * chol + .6 * smoker + .8 * diabetic
         + .04 * bmi - .1 * act + .6 * fam + r.normal(0, .3, n))
    y = (r.random(n) < _sigmoid(z)).astype(int)
    return np.column_stack([age, male, sbp, chol, smoker, diabetic, bmi, act, fam]), y


def train_all():
    os.makedirs(MODEL_DIR, exist_ok=True)
    out = {}
    for name, gen in (("diabetes", generate_diabetes), ("heart", generate_heart)):
        X, y = gen()
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=.2, stratify=y, random_state=3)
        pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        pipe.fit(X_tr, y_tr)
        auc = roc_auc_score(y_te, pipe.predict_proba(X_te)[:, 1])
        joblib.dump(pipe, os.path.join(MODEL_DIR, f"{name}_model.joblib"))
        out[name] = {"model": "Logistic Regression", "roc_auc": round(float(auc), 4),
                     "positive_rate": round(float(y.mean()), 3), "samples": int(len(y)),
                     "data": "synthetic population"}
    with open(os.path.join(MODEL_DIR, "risk_metrics.json"), "w") as f:
        json.dump(out, f, indent=2)
    return out


_cache = {}


def _model(name):
    if name not in _cache:
        path = os.path.join(MODEL_DIR, f"{name}_model.joblib")
        if not os.path.exists(path):
            train_all()
        _cache[name] = joblib.load(path)
    return _cache[name]


def metrics():
    path = os.path.join(MODEL_DIR, "risk_metrics.json")
    if not os.path.exists(path):
        train_all()
    with open(path) as f:
        return json.load(f)


def validate(name, data):
    spec = SPECS[name]
    values, errors = [], []
    for f in spec["features"]:
        lo, hi = spec["ranges"][f]
        try:
            v = float(data.get(f))
        except (TypeError, ValueError):
            errors.append(f"{spec['labels'][f]} is required")
            continue
        if not lo <= v <= hi:
            errors.append(f"{spec['labels'][f]} must be between {lo} and {hi}")
        values.append(v)
    return values, errors


def _category(p):
    if p < .15:
        return "Low"
    if p < .35:
        return "Moderate"
    if p < .60:
        return "High"
    return "Very high"


ADVICE = {
    "diabetes": {
        "Low": ["Keep a balanced diet and stay active.", "Re-check fasting glucose once a year after age 30."],
        "Moderate": ["Cut back on sugary drinks and refined carbs.", "Aim for 150 minutes of brisk activity per week.", "Get a fasting glucose / HbA1c test."],
        "High": ["Book an appointment for an HbA1c and fasting glucose test.", "Work on gradual weight loss if BMI is high.", "Follow a low-glycaemic diet."],
        "Very high": ["See a doctor soon - your inputs suggest a high chance of diabetes or pre-diabetes.", "Get confirmatory blood tests.", "Do not self-medicate."],
    },
    "heart": {
        "Low": ["Keep up regular exercise and a heart-healthy diet.", "Check blood pressure and cholesterol every year or two."],
        "Moderate": ["Reduce salt and saturated fat.", "Exercise at least 30 minutes on most days.", "Check lipid profile and BP regularly."],
        "High": ["Consult a doctor / cardiologist for a full cardiovascular check-up.", "Quit smoking if you smoke.", "Get a lipid profile and ECG."],
        "Very high": ["See a cardiologist soon for assessment.", "Do not ignore chest pain, breathlessness or fainting - seek emergency care.", "Manage BP, sugar and cholesterol strictly."],
    },
}


def predict(name, data):
    values, errors = validate(name, data)
    if errors:
        return None, errors
    spec = SPECS[name]
    pipe = _model(name)
    x = np.array([values])
    prob = float(pipe.predict_proba(x)[0, 1])
    scaler, lr = pipe.steps[0][1], pipe.steps[1][1]
    contrib = lr.coef_[0] * scaler.transform(x)[0]
    factors = []
    for f, c, v in sorted(zip(spec["features"], contrib, values), key=lambda t: -t[1]):
        factors.append({"name": spec["labels"][f], "value": v, "impact": round(float(c), 3),
                        "direction": "raises" if c > 0.05 else "lowers" if c < -0.05 else "neutral"})
    cat = _category(prob)
    return {
        "risk_percent": round(prob * 100, 1), "category": cat,
        "factors": factors[:6], "advice": ADVICE[name][cat],
    }, []
