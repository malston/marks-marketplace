# RAG (Retrieval-Augmented Generation) Reference

## When to Use RAG vs. Direct Context

| Situation | Approach |
|-----------|----------|
| < 50 pages, simple retrieval | Direct context (simpler) |
| 100+ pages or multiple docs | RAG |
| Cost-sensitive with repeated queries | RAG + prompt caching |
| Need exact term matching | Hybrid search |

## Chunking Strategies

### 1. Size-Based (most common in production)
```python
def chunk_by_size(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # overlap preserves context at boundaries
    return chunks
```
Pro: Works with any document. Con: May split mid-sentence.

### 2. Structure-Based (best for markdown/HTML)
```python
def chunk_by_section(text: str) -> list[str]:
    """Split on markdown headers."""
    import re
    sections = re.split(r'\n(?=#{1,3} )', text)
    return [s.strip() for s in sections if s.strip()]
```
Pro: Semantically meaningful chunks. Con: Requires guaranteed formatting.

### 3. Semantic-Based (most advanced)
Group consecutive sentences by semantic similarity using NLP embeddings.
Most complex to implement; use when document structure is inconsistent.

**Rule**: No universal best method — choose based on document structure guarantees.

## Embeddings

```python
import voyageai  # Anthropic-recommended embedding provider

voyage = voyageai.Client()  # set VOYAGE_API_KEY env var

def generate_embedding(text: str | list[str]) -> list[float] | list[list[float]]:
    result = voyage.embed(
        texts=[text] if isinstance(text, str) else text,
        model="voyage-3"
    )
    return result.embeddings[0] if isinstance(text, str) else result.embeddings
```

Embeddings: long float arrays (-1 to +1) representing semantic meaning.
Same model must be used for both indexing and querying.

## Vector Database (Simple Implementation)

```python
import numpy as np

class VectorIndex:
    def __init__(self):
        self.embeddings = []
        self.metadata = []

    def add_vector(self, embedding: list[float], meta: dict):
        self.embeddings.append(np.array(embedding))
        self.metadata.append(meta)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        query = np.array(query_embedding)
        scores = []
        for i, emb in enumerate(self.embeddings):
            # Cosine similarity (normalized vectors → dot product = cosine)
            similarity = np.dot(query, emb) / (np.linalg.norm(query) * np.linalg.norm(emb))
            cosine_distance = 1 - similarity  # lower = more similar
            scores.append((cosine_distance, i))
        scores.sort()
        return [self.metadata[i] for _, i in scores[:top_k]]
```

For production: use ChromaDB, Pinecone, Weaviate, or pgvector.

## BM25 Lexical Search

Complements semantic search for exact term matching:

```python
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self):
        self.docs = []
        self.index = None

    def add_document(self, text: str, meta: dict):
        self.docs.append({"text": text, "meta": meta})
        tokens = [w.lower() for w in text.split()]
        corpus = [d["text"].lower().split() for d in self.docs]
        self.index = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        tokens = query.lower().split()
        scores = self.index.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        return [(i, self.docs[i]) for i in top_indices]
```

BM25 advantages: finds exact term matches; rare terms weighted higher than common ones.

## Hybrid Search with Reciprocal Rank Fusion

```python
class HybridRetriever:
    def __init__(self):
        self.vector_index = VectorIndex()
        self.bm25_index = BM25Index()

    def add_document(self, text: str, embedding: list[float]):
        self.vector_index.add_vector(embedding, {"content": text})
        self.bm25_index.add_document(text, {"content": text})

    def search(self, query: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        # Get results from both indexes
        vec_results = self.vector_index.search(query_embedding, top_k * 2)
        bm25_results = self.bm25_index.search(query, top_k * 2)

        # Reciprocal Rank Fusion
        scores = {}
        for rank, doc in enumerate(vec_results):
            key = doc["content"]
            scores[key] = scores.get(key, 0) + 1 / (rank + 1)
        for rank, (_, doc) in enumerate(bm25_results):
            key = doc["meta"]["content"]
            scores[key] = scores.get(key, 0) + 1 / (rank + 1)

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [{"content": text} for text, _ in ranked[:top_k]]
```

RRF formula: `score = Σ 1/(rank + 1)` across all search methods per document.

## Reranking

Send hybrid results to Claude for semantic re-ordering:

```python
def rerank(query: str, candidates: list[dict], top_k: int = 3) -> list[dict]:
    doc_list = "\n".join(f"[{i}] {d['content'][:200]}" for i, d in enumerate(candidates))
    messages = [
        {"role": "user", "content": f"Query: {query}\n\nDocuments:\n{doc_list}\n\n"
                                     "Return the indices of the most relevant documents "
                                     "in decreasing order of relevance. Return only a JSON array."},
        {"role": "assistant", "content": "["}
    ]
    response = client.messages.create(
        model="claude-haiku-4-5", max_tokens=100,
        messages=messages, stop_sequences=["]"]
    )
    indices = json.loads("[" + response.content[0].text + "]")
    return [candidates[i] for i in indices[:top_k]]
```

Trade-off: extra latency for significantly improved accuracy on nuanced queries.

## Contextual Retrieval

Prepend LLM-generated context to each chunk before indexing:

```python
CONTEXT_PROMPT = """
<document>{full_document}</document>

Here is a chunk from this document:
<chunk>{chunk}</chunk>

Write 2-3 sentences explaining this chunk's role in the larger document.
Focus on what makes it uniquely retrievable. Be concise.
"""

def add_context(chunk: str, source_doc: str) -> str:
    # For large docs: include intro chunks + chunks immediately before target
    relevant_context = source_doc[:2000]  # first ~2k chars for document summary

    response = client.messages.create(
        model="claude-haiku-4-5", max_tokens=200,
        messages=[{"role": "user", "content": CONTEXT_PROMPT.format(
            full_document=relevant_context, chunk=chunk
        )}]
    )
    context = response.content[0].text
    return f"{context}\n\n{chunk}"
```

For large documents: include starter chunks (abstract/intro) + chunks immediately before the target chunk.

## Full RAG Pipeline

```python
def build_rag_pipeline(documents: list[str]) -> HybridRetriever:
    retriever = HybridRetriever()
    for doc in documents:
        chunks = chunk_by_section(doc)
        for chunk in chunks:
            contextualized = add_context(chunk, doc)
            embedding = generate_embedding(contextualized)
            retriever.add_document(contextualized, embedding)
    return retriever

def rag_query(retriever: HybridRetriever, question: str) -> str:
    query_embedding = generate_embedding(question)
    candidates = retriever.search(question, query_embedding, top_k=10)
    reranked = rerank(question, candidates, top_k=3)

    context = "\n\n---\n\n".join(d["content"] for d in reranked)
    messages = [{"role": "user", "content": f"""
Answer the question using only the provided context.

<context>{context}</context>
<question>{question}</question>
"""}]
    response = client.messages.create(model=MODEL, max_tokens=1024, messages=messages)
    return response.content[0].text
```
