"""
ChromaDB Vector Store Service
Initializes the persistent ChromaDB and seeds SBTi/CDP/IPCC benchmarks on startup.
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_client = None
_collection = None
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformer embedder (all-MiniLM-L6-v2)...")
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Embedder loaded")
        except Exception as e:
            logger.error("Failed to load embedder: %s", e)
    return _embedder


def get_collection():
    """Return (or create) the ChromaDB benchmark collection."""
    global _client, _collection

    if _collection is not None:
        return _collection

    try:
        import chromadb
        chroma_dir = os.getenv("CHROMA_DIR", "data/chroma_db")
        Path(chroma_dir).mkdir(parents=True, exist_ok=True)

        _client = chromadb.PersistentClient(path=chroma_dir)
        _collection = _client.get_or_create_collection(
            name="esg_benchmarks",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("✅ ChromaDB collection ready (docs: %d)", _collection.count())
        return _collection
    except Exception as e:
        logger.error("ChromaDB init failed: %s", e)
        return None


def seed_benchmarks() -> int:
    """Seed ground truth documents if the collection is empty. Returns count added."""
    from backend.data.ground_truth import BENCHMARK_DOCUMENTS

    collection = get_collection()
    if collection is None:
        return 0

    if collection.count() >= len(BENCHMARK_DOCUMENTS):
        logger.info("ChromaDB already seeded (%d docs)", collection.count())
        return 0

    embedder = _get_embedder()
    if embedder is None:
        logger.error("Cannot seed — embedder unavailable")
        return 0

    texts = [doc["text"] for doc in BENCHMARK_DOCUMENTS]
    ids = [doc["id"] for doc in BENCHMARK_DOCUMENTS]
    metadatas = [doc["metadata"] for doc in BENCHMARK_DOCUMENTS]

    logger.info("Embedding %d benchmark documents...", len(texts))
    embeddings = embedder.encode(texts).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    logger.info("✅ Seeded %d benchmark documents into ChromaDB", len(texts))
    return len(texts)
