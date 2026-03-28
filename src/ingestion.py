import os
import pickle
from pathlib import Path
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
POLICIES_DIR = Path("data/policies")
INDEX_DIR = Path("data/faiss_index")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
def clean_web_text(text: str) -> str:
    """
    Cleans messy text copied from real web pages.
    Removes navigation menus, repeated whitespace, cookie banners,
    footer links and other junk that appears when you copy-paste
    from a browser.
    """
    import re
    lines = text.splitlines()
    cleaned = []
    junk_patterns = [
        r"^skip to",
        r"^cookie",
        r"^accept all",
        r"^sign in",
        r"^your account",
        r"^help & customer",
        r"^back to top",
        r"^© \d{4}",
        r"^all rights reserved",
        r"^privacy notice",
        r"^conditions of use",
        r"^\s*\|\s*",
        r"^›",
        r"^Was this information helpful",
        r"^Yes\s*No\s*",
        r"^Thank you for your feedback",
        r"^\d+\s*people found this",
        r"^Share\s*$",
        r"^Print\s*$",
        r"^Feedback\s*$",
    ]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        is_junk = False
        for pattern in junk_patterns:
            if re.match(pattern, stripped, re.IGNORECASE):
                is_junk = True
                break
        if stripped.count("|") >= 3:
            is_junk = True
        if len(stripped) < 4:
            is_junk = True
        if not is_junk:
            cleaned.append(stripped)
    result = "\n".join(cleaned)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()
def load_policy_documents() -> List[Document]:
    """
    Loads all .txt policy files from POLICIES_DIR.
    Cleans the text to handle both synthetic docs and
    real web-copied policy pages.
    Returns a list of LangChain Document objects with metadata.
    """
    documents = []
    txt_files = sorted(POLICIES_DIR.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {POLICIES_DIR}")
    for filepath in txt_files:
        raw_text = filepath.read_text(encoding="utf-8", errors="ignore")
        text = clean_web_text(raw_text)
        doc_name = filepath.stem
        doc_id = doc_name
        for line in text.splitlines():
            if line.strip().startswith("Document ID:"):
                doc_id = line.strip().replace("Document ID:", "").strip()
                break
        doc = Document(
            page_content=text,
            metadata={
                "source": str(filepath),
                "filename": filepath.name,
                "doc_id": doc_id,
                "doc_name": doc_name,
            }
        )
        documents.append(doc)
        print(f"  Loaded: {filepath.name} ({len(raw_text)} → {len(text)} chars) — {doc_id}")
    return documents
def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Splits documents into chunks using RecursiveCharacterTextSplitter.
    
    Strategy:
    - chunk_size=500 characters (not tokens, but close enough for English text)
    - chunk_overlap=50 characters
    - Splits on paragraph/newline boundaries first, then sentences, then words.
    
    Each chunk keeps the parent document's metadata, plus a chunk_id.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n---\n\n", "\n\n", "\n", ". ", " ", ""],
    )
    all_chunks = []
    for doc in documents:
        chunks = splitter.split_documents([doc])
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{chunk.metadata['doc_id']}_chunk_{i:03d}"
            chunk.metadata["section"] = _extract_section_heading(chunk.page_content)
            all_chunks.append(chunk)
    return all_chunks
def _extract_section_heading(text: str) -> str:
    """
    Looks for a SECTION header in the chunk text and returns it.
    Falls back to "General" if none found.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("SECTION") or stripped.startswith("Section"):
            return stripped[:100]
    return "General"
def build_vector_store(chunks: List[Document]) -> FAISS:
    """
    Embeds chunks using HuggingFace sentence-transformers and
    stores them in a FAISS index.
    """
    print(f"\n  Loading embedding model: {EMBEDDING_MODEL} ...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print(f"  Building FAISS index from {len(chunks)} chunks ...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore
def save_vector_store(vectorstore: FAISS) -> None:
    """Saves the FAISS index to disk so we don't rebuild it every run."""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))
    print(f"  FAISS index saved to: {INDEX_DIR}")
def load_vector_store() -> FAISS:
    """Loads an existing FAISS index from disk."""
    if not INDEX_DIR.exists():
        raise FileNotFoundError(
            f"No FAISS index found at {INDEX_DIR}. "
            "Run ingestion first: python -m src.ingestion"
        )
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore
def run_ingestion():
    print("=" * 60)
    print("Amazon India Policy Ingestion Pipeline")
    print("=" * 60)
    print("\n[1/4] Loading policy documents ...")
    documents = load_policy_documents()
    print(f"      Loaded {len(documents)} documents.")
    print("\n[2/4] Chunking documents ...")
    chunks = chunk_documents(documents)
    print(f"      Created {len(chunks)} chunks.")
    print(f"      Avg chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars")
    print("\n[3/4] Building vector store ...")
    vectorstore = build_vector_store(chunks)
    print("\n[4/4] Saving FAISS index ...")
    save_vector_store(vectorstore)
    print("\nIngestion complete!")
    print(f"  Documents: {len(documents)}")
    print(f"  Chunks:    {len(chunks)}")
    print(f"  Index at:  {INDEX_DIR}")
    print("=" * 60)
if __name__ == "__main__":
    run_ingestion()