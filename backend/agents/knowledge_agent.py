import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.models.schemas import KnowledgeResult

_index = None
_texts: list[str] = []
_sources: list[str] = []
_embedder = None

def _load():
    global _index, _texts, _sources, _embedder
    if _index is None:
        _index = faiss.read_index("data/knowledge.index")
        with open("data/knowledge_meta.pkl", "rb") as f:
            meta = pickle.load(f)
        _texts = meta["texts"]
        _sources = meta["sources"]
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")

def retrieve(query: str, k: int = 2) -> KnowledgeResult:
    _load()
    query_vec = _embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, indices = _index.search(query_vec, k)

    passages = [_texts[i] for i in indices[0]]
    sources = [_sources[i] for i in indices[0]]
    confidence = float(scores[0][0])

    return KnowledgeResult(query=query, passages=passages, sources=sources, confidence=confidence)