# Vector Databases 101

A vector database stores high-dimensional embedding vectors and retrieves the
ones most similar to a query vector. They power semantic search, recommendation,
and retrieval-augmented generation (RAG) systems where meaning matters more than
exact keyword matches.

## Embeddings

An embedding model maps text, images, or audio into a fixed-length vector such
that semantically similar inputs land close together in the vector space.
Similarity is usually measured with cosine similarity or Euclidean distance.

## Approximate nearest neighbor search

Exact nearest-neighbor search is expensive at scale, so vector databases use
approximate nearest neighbor (ANN) indexes such as HNSW or IVF. These trade a
small amount of recall for dramatically faster queries over millions of vectors.

## Choosing a store

- **Managed**: Pinecone, Weaviate Cloud, and similar services handle scaling and
  operations for you.
- **Self-hosted**: Qdrant, Milvus, and pgvector (a Postgres extension) let you
  keep data in your own infrastructure.
- **In-process / library**: FAISS and Annoy are great for small or embedded use
  cases without a separate service.

## When you might not need one

For a few thousand documents, a plain in-memory matrix with cosine similarity
(as this project uses) is simpler, cheaper, and fast enough. Reach for a vector
database when your corpus, query volume, or latency budget outgrows that.
