import asyncio
from qdrant_client import AsyncQdrantClient
from FlagEmbedding import BGEM3FlagModel
from database import load_database_url
from constants import EMBEDDING_MODEL
from document_fetcher import AsyncDocumentFetcher
from retriever import AsyncRetriever


async def main():
    database_url = load_database_url()
    doc_fetcher = AsyncDocumentFetcher(database_url)

    print("Loading model...")
    model = BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=True, device='cuda')
    client = AsyncQdrantClient(host="localhost", port=6334, prefer_grpc=True)

    retriever = AsyncRetriever(client, model, doc_fetcher)

    try:
        query = "Установление дискриминационных условий в договоре поставки"
        print(f"Searching for: {query}...")

        results = await retriever.search(query, limit=5)

        for res in results:
            print(f"\n--- Doc: {res['doc_id']} (Score: {res['score']:.3f}) ---")
            print(f"Chunk: {res['best_chunk']}...")
            if res['full_text']:
                print(f"Full Text preview: {res['full_text'][:100]}...")
            else:
                print("Full text not found.")

    finally:
        await client.close()
        await doc_fetcher.close()

if __name__ == "__main__":
    asyncio.run(main())
