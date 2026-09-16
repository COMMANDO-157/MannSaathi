import faiss
import numpy as np
from backend.models.schemas import KnowledgeResult

_index = None
_documents: list[str] = []
_sources: list[str] = []

def load_index(index_path: str, docs: list[str], sources: list[str]):
    global _index, _documents, _sources
    _index = faiss.read_index(index_path)
    _documents = docs
    _sources = sources

def embed_query(query: str) -> np.ndarray:
    # TODO: plug in real embedding model (e.g. sentence-transformers)
    raise NotImplementedError

def retrieve(query: str, k: int = 3) -> KnowledgeResult:
    query_vec = embed_query(query)
    distances, indices = _index.search(query_vec, k)
    passages = [_documents[i] for i in indices[0]]
    sources = [_sources[i] for i in indices[0]]
    confidence = float(1.0 / (1.0 + distances[0][0]))
    return KnowledgeResult(query=query, passages=passages, sources=sources, confidence=confidence)