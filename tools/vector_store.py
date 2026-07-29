"""
Profile vector store — **LlamaIndex ingestion** + Chroma + HuggingFace embeddings.

LlamaIndex owns the ingestion pipeline: profile text is loaded as LlamaIndex
``Document`` objects, chunked by a ``SentenceSplitter`` node parser, embedded with
a local HuggingFace model, and persisted into a local Chroma collection through
``ChromaVectorStore``. Retrieval uses LlamaIndex's ``VectorStoreIndex`` retriever
with metadata filtering (IC vs Leadership).

Everything runs locally — no external embedding API, no cloud vector DB.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
import chromadb
from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
# New collection name (LlamaIndex-managed schema) — distinct from the legacy
# LangChain "profiles" collection so the two schemas never clash.
PROFILE_COLLECTION = os.getenv("PROFILE_COLLECTION", "profiles_li")

IC_PROFILE_PATH = os.getenv("IC_PROFILE_PATH", "../Profile Summary - IC.txt")
LEADERSHIP_PROFILE_PATH = os.getenv(
    "LEADERSHIP_PROFILE_PATH", "../Profile Summary-Leadership.txt")

# Local embeddings — runs on CPU, no API key required
# Model: all-MiniLM-L6-v2 (~80MB, downloaded once, cached locally)
_embed_model = None
_index = None


def get_embeddings() -> HuggingFaceEmbedding:
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            device="cpu",
            normalize=True,
        )
        # Ensure LlamaIndex never falls back to a remote (OpenAI) embed model.
        Settings.embed_model = _embed_model
    return _embed_model


def _load_profile_docs() -> list[Document]:
    """Load IC and Leadership profile text files as LlamaIndex Documents."""
    docs: list[Document] = []

    for label, path_str in [
        ("IC", IC_PROFILE_PATH),
        ("Leadership", LEADERSHIP_PROFILE_PATH),
    ]:
        path = Path(path_str)
        if not path.exists():
            # Try resolving relative to this file's location
            path = Path(__file__).parent.parent / path_str.lstrip("../")

        if path.exists():
            text = path.read_text(encoding="utf-8")
            docs.append(
                Document(
                    text=text,
                    metadata={"profile_type": label, "source": str(path)},
                    # Keep "source" out of the embedded/LLM text — it's noise.
                    excluded_embed_metadata_keys=["source"],
                    excluded_llm_metadata_keys=["source"],
                )
            )
        else:
            print(f"⚠️  Profile not found: {path_str}")

    return docs


def _chroma_collection(reset: bool = False):
    """Return the persistent Chroma collection, optionally wiping it first."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    if reset:
        try:
            client.delete_collection(PROFILE_COLLECTION)
        except Exception:
            pass
    return client.get_or_create_collection(PROFILE_COLLECTION)


def _build_index(reset: bool = False) -> VectorStoreIndex:
    """
    Build (or load) the LlamaIndex VectorStoreIndex backed by Chroma.

    - If the collection is empty (or reset=True), run the LlamaIndex ingestion
      pipeline: load docs → SentenceSplitter chunking → embed → persist to Chroma.
    - Otherwise, attach to the existing Chroma collection without re-embedding.
    """
    embed_model = get_embeddings()
    collection = _chroma_collection(reset=reset)
    vector_store = ChromaVectorStore(chroma_collection=collection)

    if reset or collection.count() == 0:
        print("🔧 Ingesting profiles with LlamaIndex → Chroma ...")
        docs = _load_profile_docs()
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store)
        index = VectorStoreIndex.from_documents(
            docs,
            storage_context=storage_context,
            transformations=[splitter],
            embed_model=embed_model,
        )
        print(f"✅ Ingested {len(docs)} profile document(s) "
              f"→ {collection.count()} chunks in Chroma")
    else:
        index = VectorStoreIndex.from_vector_store(
            vector_store, embed_model=embed_model)

    return index


def get_profile_index() -> VectorStoreIndex:
    """Return a cached LlamaIndex index over the IC + Leadership profiles."""
    global _index
    if _index is None:
        _index = _build_index(reset=False)
    return _index


def search_profiles(query: str, profile_type: str, k: int = 3) -> list[str]:
    """
    Retrieve the top-k most relevant profile chunks for a given profile type
    ("IC" or "Leadership") using LlamaIndex semantic retrieval over Chroma.

    Returns a list of plain-text chunk contents (empty list if nothing found).
    """
    index = get_profile_index()
    filters = MetadataFilters(
        filters=[MetadataFilter(
            key="profile_type", value=profile_type,
            operator=FilterOperator.EQ)]
    )
    retriever = index.as_retriever(similarity_top_k=k, filters=filters)
    nodes = retriever.retrieve(query)
    return [n.node.get_content() for n in nodes]


def refresh_profiles() -> VectorStoreIndex:
    """Force-reingest profiles into Chroma (use after profile edits)."""
    global _index
    _index = _build_index(reset=True)
    return _index
