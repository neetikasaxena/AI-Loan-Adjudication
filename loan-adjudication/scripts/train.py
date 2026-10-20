"""Train the learned baselines the hybrid pipeline is compared against.

  tfidf_lr         original end-to-end text classifier (word + char n-grams, fixed C=4)
  tfidf_lr_cv      regularised text classifier: digits masked, word n-grams, C/max_features/min_df by 5-fold CV
  tree_structured  regex-extracted facts -> numeric features -> depth-limited decision tree tuned by 5-fold CV
  tree_on_truth    diagnostic upper bound: the same tree trained/evaluated on the true facts

Models are saved to models/<name>.joblib (all take raw text except tree_on_truth); metrics to
reports/training_metrics.json and the learned tree to reports/tree_rules.txt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.tree import DecisionTreeClassifier, export_text

from loan_adjudication import PROJECT_ROOT
from loan_adjudication.features import FEATURE_NAMES, applications_to_features, mask_digits, texts_to_features

LABELS = ["APPROVE", "FLAG_REVIEW", "REJECT"]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]

def model_text(record: dict) -> str:
    """Identity-masked text, so the classifier cannot use names or cities as shortcuts."""
    return record.get("narrative_masked", record["narrative"])

def tfidf_lr() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
    ])
    return Pipeline([("features", features), ("clf", LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced"))])

def tfidf_lr_cv() -> GridSearchCV:
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(preprocessor=mask_digits, ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=3000, class_weight="balanced")),
    ])
    grid = {"tfidf__max_features": [2000, 5000, None], "tfidf__min_df": [2, 5], "clf__C": [0.1, 0.3, 1.0, 3.0]}
    return GridSearchCV(pipe, grid, cv=CV, scoring="f1_macro", n_jobs=-1, return_train_score=True)

def tree(feature_step: bool) -> GridSearchCV:
    clf = DecisionTreeClassifier(class_weight="balanced", random_state=0)
    steps = ([("features", FunctionTransformer(texts_to_features))] if feature_step else []) + [("clf", clf)]
    grid = {"clf__max_depth": [3, 4, 6, 8, 10, None], "clf__min_samples_leaf": [1, 5, 10, 20]}
    return GridSearchCV(Pipeline(steps), grid, cv=CV, scoring="f1_macro", n_jobs=-1, return_train_score=True)

def summarise(name: str, model, x_train, y_train, x_val, y_val) -> dict:
    train_pred, val_pred = model.predict(x_train), model.predict(x_val)
    row = {
        "train_accuracy": round(accuracy_score(y_train, train_pred), 4),
        "val_accuracy": round(accuracy_score(y_val, val_pred), 4),
        "val_macro_f1": round(f1_score(y_val, val_pred, labels=LABELS, average="macro"), 4),
        "val_false_approvals": int(sum(t != "APPROVE" and p == "APPROVE" for t, p in zip(y_val, val_pred))),
    }
    row["train_val_gap"] = round(row["train_accuracy"] - row["val_accuracy"], 4)
    if isinstance(model, GridSearchCV):
        i = model.best_index_
        row["cv_macro_f1"] = f"{model.cv_results_['mean_test_score'][i]:.3f} ± {model.cv_results_['std_test_score'][i]:.3f}"
        row["best_params"] = {k.split("__")[-1]: v for k, v in model.best_params_.items()}
    print(f"{name:<16} train={row['train_accuracy']:.3f} val={row['val_accuracy']:.3f} gap={row['train_val_gap']:+.3f}"
          f" val_f1={row['val_macro_f1']:.3f} false_approvals={row['val_false_approvals']:>3}"
          f" cv_f1={row.get('cv_macro_f1', '-')} {row.get('best_params', '')}")
    return row

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default=str(PROJECT_ROOT / "data" / "processed"))
    parser.add_argument("--models-dir", default=str(PROJECT_ROOT / "models"))
    parser.add_argument("--reports-dir", default=str(PROJECT_ROOT / "reports"))
    args = parser.parse_args()

    data, models_dir, reports = Path(args.data), Path(args.models_dir), Path(args.reports_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    train, val = load(data / "train.jsonl"), load(data / "val.jsonl")
    y_train, y_val = np.array([r["label"] for r in train]), np.array([r["label"] for r in val])
    text_train, text_val = [model_text(r) for r in train], [model_text(r) for r in val]

    results = {}
    for name, model in (("tfidf_lr", tfidf_lr()), ("tfidf_lr_cv", tfidf_lr_cv()), ("tree_structured", tree(True))):
        model.fit(text_train, y_train)
        results[name] = summarise(name, model, text_train, y_train, text_val, y_val)
        joblib.dump(model.best_estimator_ if isinstance(model, GridSearchCV) else model, models_dir / f"{name}.joblib")

    truth_model = tree(False)
    x_train = applications_to_features([r["truth"] for r in train])
    x_val = applications_to_features([r["truth"] for r in val])
    truth_model.fit(x_train, y_train)
    results["tree_on_truth"] = summarise("tree_on_truth", truth_model, x_train, y_train, x_val, y_val)
    learned = truth_model.best_estimator_.named_steps["clf"]
    (reports / "tree_rules.txt").write_text(export_text(learned, feature_names=list(FEATURE_NAMES)))

    (reports / "training_metrics.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved models to {models_dir}; metrics to {reports / 'training_metrics.json'}")

if __name__ == "__main__":
    main()
