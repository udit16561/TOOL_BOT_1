from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityRouter:
    def __init__(self, examples: dict):
        """
        examples = {
            "currency": [list of example queries],
            "market": [...],
            "scholar": [...],
            "paper_detail": [...]
        }
        """
        self.labels = []
        self.texts = []

        for label, queries in examples.items():
            for q in queries:
                self.labels.append(label)
                self.texts.append(q)

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.vectors = self.vectorizer.fit_transform(self.texts)

    def route(self, query: str, threshold: float = 0.25):
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.vectors)[0]

        best_idx = sims.argmax()
        if sims[best_idx] < threshold:
            return None

        return self.labels[best_idx]