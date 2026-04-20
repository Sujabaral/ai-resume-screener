import os
import math
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score


DATA_PATH = "data/domain_dataset.csv"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "domain_classifier.pkl")


def load_dataset(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required_columns = {"text", "domain"}
    if not required_columns.issubset(df.columns):
        raise ValueError(
            f"CSV must contain columns: {required_columns}. Found: {set(df.columns)}"
        )

    df = df.dropna(subset=["text", "domain"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df["domain"] = df["domain"].astype(str).str.strip()
    df = df[(df["text"] != "") & (df["domain"] != "")]

    return df


def validate_dataset(df: pd.DataFrame) -> None:
    class_counts = df["domain"].value_counts()
    rare_classes = class_counts[class_counts < 2]

    if not rare_classes.empty:
        raise ValueError(
            "Each class must have at least 2 samples for stratified train/test split.\n"
            f"Classes with too few samples:\n{rare_classes.to_string()}"
        )


def get_safe_test_size(df: pd.DataFrame, base_ratio: float = 0.2) -> int:
    """
    Return a safe integer test size for stratified splitting.
    It must be:
    - at least number of classes
    - based on base_ratio
    - leave enough room for training
    """
    n_samples = len(df)
    n_classes = df["domain"].nunique()

    base_test_size = math.ceil(n_samples * base_ratio)
    safe_test_size = max(base_test_size, n_classes)

    # Keep enough room so train split still has representation
    max_allowed_test = n_samples - n_classes
    if safe_test_size > max_allowed_test:
        safe_test_size = max_allowed_test

    if safe_test_size < n_classes:
        raise ValueError(
            f"Dataset too small for stratified split: "
            f"{n_samples} samples, {n_classes} classes."
        )

    return safe_test_size


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    max_features=5000,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def train_model(df: pd.DataFrame) -> Pipeline:
    validate_dataset(df)

    X = df["text"]
    y = df["domain"]

    n_classes = y.nunique()
    test_size = get_safe_test_size(df, base_ratio=0.2)

    print(f"Total samples: {len(df)}")
    print(f"Total classes: {n_classes}")
    print(f"Using stratified test_size: {test_size}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=42,
        stratify=y,
    )

    model = build_pipeline()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\n===== Domain Classifier Evaluation =====")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}\n")
    print(classification_report(y_test, y_pred, zero_division=0))

    return model


def save_model(model: Pipeline, model_path: str) -> None:
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    print(f"\nModel saved to: {model_path}")


def test_predictions(model: Pipeline) -> None:
    sample_jobs = [
        "Looking for a content creator intern with social media management, branding, copywriting, and campaign planning skills.",
        "Need a Python backend developer experienced in Flask, REST APIs, SQL, and deployment.",
        "Seeking HR assistant for onboarding, recruitment support, interview scheduling, and employee coordination.",
        "Hiring data analyst with Excel, SQL, dashboarding, KPI tracking, and reporting skills.",
        "Need customer support associate for handling client complaints, tickets, and live chat queries.",
    ]

    print("\n===== Sample Predictions =====")
    for job in sample_jobs:
        pred = model.predict([job])[0]
        probs = model.predict_proba([job])[0]
        classes = model.classes_

        top_idx = probs.argmax()
        confidence = probs[top_idx]

        top_pairs = sorted(
            zip(classes, probs),
            key=lambda x: x[1],
            reverse=True,
        )[:3]

        print(f"\nText: {job}")
        print(f"Predicted Domain: {pred}")
        print(f"Confidence: {confidence:.4f}")
        print("Top 3 domain probabilities:")
        for label, prob in top_pairs:
            print(f"  - {label}: {prob:.4f}")


def main() -> None:
    print("Loading dataset...")
    df = load_dataset(DATA_PATH)
    print(f"Loaded {len(df)} rows.")

    print("Training domain classifier...")
    model = train_model(df)

    print("Saving model...")
    save_model(model, MODEL_PATH)

    test_predictions(model)


if __name__ == "__main__":
    main()