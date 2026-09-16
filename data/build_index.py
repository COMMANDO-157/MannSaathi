"""
One-time script to build the FAISS index from the knowledge base.
Run with: python -m data.build_index
"""
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from data.knowledge_base import KNOWLEDGE_BASE

def build():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [entry[0] for entry in KNOWLEDGE_BASE]
    sources = [entry[1] for entry in KNOWLEDGE_BASE]

    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine similarity
    index.add(embeddings)

    faiss.write_index(index, "data/knowledge.index")
    with open("data/knowledge_meta.pkl", "wb") as f:
        pickle.dump({"texts": texts, "sources": sources}, f)

    print(f"Built index with {len(texts)} entries.")

if __name__ == "__main__":
    build()