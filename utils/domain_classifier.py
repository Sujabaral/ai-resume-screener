import os
import joblib
from typing import Dict, List, Optional


MODEL_PATH = os.path.join("models", "domain_classifier.pkl")


class DomainClassifier:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False

    def load(self) -> None:
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Domain classifier model not found at: {self.model_path}\n"
                "Train it first using: python training/train_domain_classifier.py"
            )

        self.model = joblib.load(self.model_path)
        self.is_loaded = True

    def predict(self, text: str) -> Dict:
        if not text or not text.strip():
            return {
                "domain": "unknown",
                "confidence": 0.0,
                "top_predictions": []
            }

        if not self.is_loaded:
            self.load()

        probs = self.model.predict_proba([text])[0]
        classes = list(self.model.classes_)

        top_idx = probs.argmax()
        top_domain = classes[top_idx]
        top_confidence = float(probs[top_idx])

        ranked = sorted(
            zip(classes, probs),
            key=lambda x: x[1],
            reverse=True
        )

        top_predictions: List[Dict] = [
            {
                "domain": label,
                "confidence": round(float(prob), 4)
            }
            for label, prob in ranked[:3]
        ]

        return {
            "domain": top_domain,
            "confidence": round(top_confidence, 4),
            "top_predictions": top_predictions
        }


_classifier_instance: Optional[DomainClassifier] = None


def get_domain_classifier() -> DomainClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = DomainClassifier()
    return _classifier_instance


def predict_job_domain(text: str) -> Dict:
    try:
        classifier = get_domain_classifier()
        return classifier.predict(text)
    except Exception as e:
        return {
            "domain": "unknown",
            "confidence": 0.0,
            "top_predictions": [],
            "error": str(e)
        }


def get_domain_confidence(text: str) -> float:
    result = predict_job_domain(text)
    return round(float(result.get("confidence", 0.0)), 4)


def get_domain_label(text: str) -> str:
    result = predict_job_domain(text)
    return result.get("domain", "unknown")


def get_top_domain_predictions(text: str) -> List[Dict]:
    result = predict_job_domain(text)
    return result.get("top_predictions", [])