"""
Knowledge Base Builder for Healthmov Insight Engine.

Downloads content from URLs (PDFs and web pages),
saves them as .txt files, chunks them, embeds them,
and stores vectors in MongoDB Atlas Vector Search.

Usage:
       python rag/build_knowledge_base.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import pdfplumber
import io
from bs4 import BeautifulSoup
from datetime import datetime
from sentence_transformers import SentenceTransformer
from database.connection import get_collection, test_connection

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

KNOWLEDGE_BASE_COLLECTION = "health_knowledge"  # Collection for RAG embeddings

DOCUMENTS = [
    # Physical Activity
    {
        "url": "https://odphp.health.gov/sites/default/files/2019-09/Physical_Activity_Guidelines_2nd_edition.pdf",
        "title": "Physical Activity Guidelines for Americans 2nd Edition",
        "category": "physical_activity",
        "type": "pdf"
    },
    {
        "url": "https://www.cdc.gov/physical-activity-basics/measuring/index.html",
        "title": "CDC Measuring Physical Activity Intensity",
        "category": "physical_activity",
        "type": "web"
    },
    # Sleep
    {
        "url": "https://www.nhlbi.nih.gov/files/docs/public/sleep/healthy_sleep.pdf",
        "title": "NIH Your Guide to Healthy Sleep",
        "category": "sleep",
        "type": "pdf"
    },
    {
        "url": "https://www.fammed.wisc.edu/files/webfm-uploads/documents/outreach/im/handout_sleep.pdf",
        "title": "Sleep Hygiene Handout UW Family Medicine",
        "category": "sleep",
        "type": "pdf"
    },
    # Heart Rate
    {
        "url": "https://www.mdanderson.org/cancerwise/how-to-get-your-heart-rate-up.h00-159775656.html",
        "title": "MD Anderson How to Get Your Heart Rate Up",
        "category": "heart_rate",
        "type": "web"
    },
    {
        "url": "https://www.health.harvard.edu/blog/increase-in-resting-heart-rate-is-a-signal-worth-watching-201112214013",
        "title": "Harvard Health Resting Heart Rate Signal",
        "category": "heart_rate",
        "type": "web"
    },
]

CHUNK_SIZE = 500      # words per chunk
CHUNK_OVERLAP = 50    # words overlap between chunks

# ──────────────────────────────────────────────
# 1. Fetch Content
# ──────────────────────────────────────────────

def fetch_pdf(url: str) -> str:
    """Download a PDF from a URL and extract its text."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        return text.strip()
    except Exception as e:
        print(f"    [ERROR] PDF fetch failed: {e}")
        return ""


def fetch_webpage(url: str) -> str:
    """Fetch a webpage and extract its main text content."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove navigation, scripts, styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        # Clean up excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text).strip()

        return text
    except Exception as e:
        print(f"    [ERROR] Webpage fetch failed: {e}")
        return ""


def fetch_document(doc: dict) -> str:
    """Fetch content from a document based on its type."""
    print(f"  Fetching: {doc['title']}")
    try:
        if doc["type"] == "pdf":
            return fetch_pdf(doc["url"])
        else:
            return fetch_webpage(doc["url"])
    except Exception as e:
        print(f"  [WARN] Failed to fetch {doc['title']}: {e}")
        return ""


# ──────────────────────────────────────────────
# 2. Save as .txt
# ──────────────────────────────────────────────

def save_as_txt(title: str, content: str, output_dir: str) -> str:
    """Save document content as a .txt file."""
    filename = title.lower().replace(" ", "_").replace("/", "_") + ".txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  [OK] Saved to {filepath} ({len(content)} chars)")
    return filepath


# ──────────────────────────────────────────────
# 3. Chunk Text
# ──────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# ──────────────────────────────────────────────
# 4. Embed & Store in MongoDB
# ──────────────────────────────────────────────

def embed_and_store(doc: dict, chunks: list, model):
    """Embed chunks using sentence-transformers and store in MongoDB Atlas Vector Search."""
    collection = get_collection(KNOWLEDGE_BASE_COLLECTION)

    # Delete existing chunks for this document to avoid duplicates on re-run
    collection.delete_many({"source_url": doc["url"]})

    stored = 0
    for i, chunk in enumerate(chunks):
        # Generate embedding using sentence-transformers (384 dimensions)
        embedding = model.encode(chunk).tolist()

        # Store in MongoDB
        collection.insert_one({
            "title": doc["title"],
            "category": doc["category"],
            "source_url": doc["url"],
            "chunk_index": i,
            "total_chunks": len(chunks),
            "text": chunk,
            "embedding": embedding,
            "created_at": datetime.now().isoformat()
        })
        stored += 1

    print(f"  [OK] Stored {stored} chunks in MongoDB")
    return stored


# ──────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────

def build_knowledge_base():
    print("=" * 60)
    print("Healthmov — Knowledge Base Builder")
    print("=" * 60)

    # Test MongoDB connection
    print("\n1. Testing MongoDB connection...")
    result = test_connection()
    if result["status"] != "connected":
        print(f"  [FAIL] {result['error']}")
        sys.exit(1)
    print(f"  [OK] Connected to MongoDB")

    # Initialize embedding model
    print("\n2. Initializing embedding model...")
    
    # Load a lightweight, high-quality model (384 dimensions)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("  [OK] Loaded sentence-transformers model: all-MiniLM-L6-v2")
    print("  [INFO] Embedding dimensions: 384")

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "txt_files")
    os.makedirs(output_dir, exist_ok=True)

    # Process each document
    print(f"\n3. Processing {len(DOCUMENTS)} documents...")
    total_chunks = 0

    for doc in DOCUMENTS:
        print(f"\n  [{doc['category'].upper()}] {doc['title']}")

        # Fetch content
        content = fetch_document(doc)
        if not content:
            print(f"  [SKIP] No content retrieved")
            continue

        # Save as .txt
        save_as_txt(doc["title"], content, output_dir)

        # Chunk
        chunks = chunk_text(content)
        print(f"  [OK] Created {len(chunks)} chunks")

        # Embed and store
        embed_and_store(doc, chunks, model)
        total_chunks += len(chunks)

    print(f"\n{'='*60}")
    print(f"[OK] Knowledge base built: {total_chunks} total chunks stored in MongoDB")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    build_knowledge_base()
