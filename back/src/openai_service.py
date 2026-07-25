import os
import json
from typing import Any, List, Tuple

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class OpenAIService:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and OpenAI is not None:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception:
                self.client = None
        else:
            self.client = None

    def _get_embedding(self, text: str) -> List[float]:
        if self.client is not None:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding
        # Fallback: simple token-based vector (term frequencies). Caller must use consistent method.
        # We'll return a list of token counts for the most common tokens; but for full search we compute TF-IDF in search_similar.
        tokens = self._tokenize(text)
        # return small vector of token counts (not used when fallback TF-IDF is applied)
        return [len(tokens)]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def search_similar(self, payload: Any, reference_text: str, top_k: int = 5) -> Any:
        if not isinstance(payload, list):
            raise ValueError("The JSON payload must be a list of records")

        if len(payload) == 0:
            raise ValueError("The JSON payload must contain at least one record")

        if not reference_text or not reference_text.strip():
            raise ValueError("Reference text is required")

        if len(payload) <= top_k:
            return payload

        # If OpenAI client available, use embeddings API; otherwise use local TF-IDF fallback
        records_with_score: List[Tuple[float, Any]] = []

        if self.client is not None:
            try:
                reference_embedding = self._get_embedding(reference_text)
                for item in payload:
                    text_representation = self._build_text_representation(item)
                    embedding = self._get_embedding(text_representation)
                    score = self._cosine_similarity(reference_embedding, embedding)
                    records_with_score.append((score, item))
            except Exception:
                # if OpenAI call fails (quota, network), fallback to local TF-IDF
                self.client = None

        if self.client is None:
            # local TF-IDF fallback
            docs = [reference_text] + [self._build_text_representation(item) for item in payload]
            vectors = self._tfidf_vectors(docs)
            ref_vec = vectors[0]
            for idx, item in enumerate(payload, start=1):
                vec = vectors[idx]
                score = self._cosine_similarity(ref_vec, vec)
                records_with_score.append((score, item))

        records_with_score.sort(key=lambda entry: entry[0], reverse=True)
        top_items = [item for _, item in records_with_score[:top_k]]
        return top_items

    def _tokenize(self, text: str) -> List[str]:
        # simple lowercase tokenization on non-alphanumerics
        import re

        tokens = re.findall(r"\w+", text.lower())
        return tokens

    def _tfidf_vectors(self, docs: List[str]) -> List[List[float]]:
        # compute TF-IDF vectors without external deps
        from math import log
        tokenized = [self._tokenize(d) for d in docs]
        # build vocabulary
        vocab = {}
        for doc in tokenized:
            for t in doc:
                if t not in vocab:
                    vocab[t] = len(vocab)

        N = len(tokenized)
        df = [0] * len(vocab)
        for doc in tokenized:
            seen = set()
            for t in doc:
                if t not in seen:
                    df[vocab[t]] += 1
                    seen.add(t)

        idf = [0.0] * len(vocab)
        for term, idx in vocab.items():
            idf[idx] = log((N + 1) / (df[idx] + 1)) + 1

        vectors: List[List[float]] = []
        for doc in tokenized:
            tf = [0.0] * len(vocab)
            for t in doc:
                tf[vocab[t]] += 1.0
            # normalize TF
            doc_len = sum(tf) if sum(tf) > 0 else 1.0
            tf = [x / doc_len for x in tf]
            vec = [tf[i] * idf[i] for i in range(len(vocab))]
            vectors.append(vec)
        return vectors

    def _build_text_representation(self, item: Any) -> str:
        if isinstance(item, dict):
            values = []
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value, ensure_ascii=False))
                else:
                    values.append(str(value))
            return " ".join(values)
        if isinstance(item, list):
            return json.dumps(item, ensure_ascii=False)
        return str(item)
