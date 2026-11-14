"""Symptom -> disease model.

Bernoulli Naive Bayes trained on a synthetic dataset generated from
`knowledge.py`. Inference supports *partial evidence*: symptoms the user did
not mention are treated as "unknown", not "absent" - only symptoms the user
explicitly said they do NOT have count as absent. This makes the chatbot's
follow-up questions meaningful.
"""
import json
import os

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import BernoulliNB

from .knowledge import DISEASES, SYMPTOMS

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(os.path.dirname(HERE), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "symptom_model.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "symptom_metrics.json")

SYMPTOM_KEYS = list(SYMPTOMS.keys())
DISEASE_NAMES = list(DISEASES.keys())
NOISE_P = 0.03  # chance of any unrelated symptom appearing


def generate_dataset(n_per_disease=500, seed=42):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for d_idx, name in enumerate(DISEASE_NAMES):
        profile = DISEASES[name]["symptoms"]
        probs = np.array([profile.get(s, NOISE_P) for s in SYMPTOM_KEYS])
        samples = (rng.random((n_per_disease, len(SYMPTOM_KEYS))) < probs).astype(int)
        # every patient has at least one symptom
        empty = samples.sum(axis=1) == 0
        for i in np.where(empty)[0]:
            samples[i, rng.choice(np.where(probs > .5)[0])] = 1
        X.append(samples)
        y.extend([d_idx] * n_per_disease)
    return np.vstack(X), np.array(y)


def train(save=True):
    X, y = generate_dataset()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=7)
    clf = BernoulliNB(alpha=1.0).fit(X_tr, y_tr)
    pred = clf.predict(X_te)
    metrics = {
        "model": "Bernoulli Naive Bayes",
        "diseases": len(DISEASE_NAMES),
        "symptoms": len(SYMPTOM_KEYS),
        "train_samples": int(len(X_tr)),
        "test_samples": int(len(X_te)),
        "accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "macro_f1": round(float(f1_score(y_te, pred, average="macro")), 4),
        "data": "synthetic (generated from knowledge base)",
    }
    bundle = {"clf": clf}
    if save:
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(bundle, MODEL_PATH)
        with open(METRICS_PATH, "w") as f:
            json.dump(metrics, f, indent=2)
    return bundle, metrics


_bundle = None


def load():
    global _bundle
    if _bundle is None:
        if os.path.exists(MODEL_PATH):
            _bundle = joblib.load(MODEL_PATH)
        else:
            _bundle, _ = train()
    return _bundle


def metrics():
    if not os.path.exists(METRICS_PATH):
        train()
    with open(METRICS_PATH) as f:
        return json.load(f)


def predict(present, absent=()):
    """Return ranked [(disease, probability)] given sets of symptom keys."""
    clf = load()["clf"]
    log_p = clf.feature_log_prob_                      # log P(symptom | disease)
    log_not_p = np.log1p(-np.exp(log_p))              # log P(no symptom | disease)
    score = clf.class_log_prior_.copy()
    for i, s in enumerate(SYMPTOM_KEYS):
        if s in present:
            score += log_p[:, i]
        elif s in absent:
            score += log_not_p[:, i]
    score -= score.max()
    probs = np.exp(score)
    probs /= probs.sum()
    order = np.argsort(-probs)
    return [(DISEASE_NAMES[i], float(probs[i])) for i in order]


def next_question(present, absent, asked, top_n=3):
    """Pick the unasked symptom that best separates the leading diseases."""
    ranked = predict(present, absent)[:top_n]
    best, best_score = None, 0.0
    for s in SYMPTOM_KEYS:
        if s in present or s in absent or s in asked:
            continue
        sc = sum(p * DISEASES[d]["symptoms"].get(s, 0) for d, p in ranked)
        if sc > best_score:
            best, best_score = s, sc
    return best
