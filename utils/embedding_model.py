from typing import List, Union, Optional, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingModel:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.is_loaded = False

    def load(self) -> None:
        if not self.is_loaded:
            self.model = SentenceTransformer(self.model_name)
            self.is_loaded = True

    def encode(
        self,
        texts: Union[str, List[str]],
        normalize_embeddings: bool = True
    ) -> np.ndarray:
        if not self.is_loaded:
            self.load()

        if isinstance(texts, str):
            texts = [texts]

        cleaned_texts = [
            text.strip() if isinstance(text, str) and text.strip() else " "
            for text in texts
        ]

        embeddings = self.model.encode(
            cleaned_texts,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings

    def similarity(self, text_a: str, text_b: str) -> float:
        embeddings = self.encode([text_a, text_b], normalize_embeddings=True)
        score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return round(float(score), 4)

    def batch_similarity(
        self,
        source_text: str,
        target_texts: List[str]
    ) -> List[float]:
        if not target_texts:
            return []

        all_texts = [source_text] + target_texts
        embeddings = self.encode(all_texts, normalize_embeddings=True)

        source_vec = embeddings[0].reshape(1, -1)
        target_vecs = embeddings[1:]

        scores = cosine_similarity(source_vec, target_vecs)[0]
        return [round(float(score), 4) for score in scores]

    def best_match(
        self,
        source_text: str,
        candidates: List[str]
    ) -> Dict:
        if not candidates:
            return {
                "text": "",
                "score": 0.0,
                "index": -1
            }

        scores = self.batch_similarity(source_text, candidates)
        best_index = int(np.argmax(scores))
        return {
            "text": candidates[best_index],
            "score": round(float(scores[best_index]), 4),
            "index": best_index
        }


_embedding_instance: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = EmbeddingModel()
    return _embedding_instance


def encode_text(text: str) -> np.ndarray:
    model = get_embedding_model()
    return model.encode(text)


def compute_similarity(text_a: str, text_b: str) -> float:
    model = get_embedding_model()
    return model.similarity(text_a, text_b)


def compute_batch_similarity(source_text: str, target_texts: List[str]) -> List[float]:
    model = get_embedding_model()
    return model.batch_similarity(source_text, target_texts)