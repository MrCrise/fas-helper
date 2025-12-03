import time
from qdrant_client import AsyncQdrantClient
from database import load_database_url
from document_fetcher import AsyncDocumentFetcher
from FlagEmbedding import BGEM3FlagModel
from constants import EMBEDDING_MODEL
from llm_service import AsyncLLMService
from retriever import AsyncRetriever


class AsyncRAG:
    def __init__(self):
        self.db_url = load_database_url()
        self.doc_fetcher = None
        self.client = None
        self.model = None
        self.retriever = None
        self.llm = None

    async def initialize(self):
        """
        Инициализирует все подключения и модели.
        """

        print(" [1/4] Connecting to PostgreSQL", end=" ", flush=True)
        self.doc_fetcher = AsyncDocumentFetcher(self.db_url)
        await self.doc_fetcher._get_table()
        print("OK")

        print(" [2/4] Loading embedding model", end=" ", flush=True)
        self.model = BGEM3FlagModel(
            EMBEDDING_MODEL, use_fp16=True, device='cuda')
        print("OK")

        print(" [3/4] Connecting to Qdrant", end=" ", flush=True)
        self.client = AsyncQdrantClient(
            host="localhost", port=6334, prefer_grpc=True)
        self.retriever = AsyncRetriever(
            self.client, self.model, self.doc_fetcher)
        print("OK")

        print(" [4/4] Initializing Ollama", end=" ", flush=True)
        self.llm = AsyncLLMService(
            llm_host="http://localhost:11434",
            model_name="qwen3:8b",
            context_window_size=20000
        )
        print("OK")
        print("-" * 50)

    async def process_query(self, query: str) -> None:
        """
        Обрабатывает один запрос.
        """

        start_time = time.time()
        print(f"Searching for: {query}")

        try:
            search_results = await self.retriever.search(query=query)
        except Exception as e:
            print(f"Searching error: {e}")
            return

        search_time = start_time - time.time()

        if not search_results:
            print("Docs not found")

        print(f"Found {len(search_results)} docs in {search_time} secs")
        for res in search_results:
            print(
                f"\n--- Doc: {res['doc_id']} (Score: {res['score']:.3f}) ---")
            print(f"Chunk: {res['best_chunk']}...")
            if res['full_text']:
                print(f"Full Text preview: {res['full_text'][:100]}...")
            else:
                print("Full text not found")

        print("LLM generation started")
        print("-" * 50)

        full_response = ""
        try:
            async for chunk in self.llm.generate_stream(query=query, documents=search_results):
                print(chunk, end="", flush=True)
                full_response += chunk
        except Exception as e:
            print(f"LLM generation error: {e}")

        print("\n" + "-" * 60)
        total_time = time.time() - start_time
        print(f"Total time elapsed: {total_time}")

    async def close(self) -> None:
        """
        Закрывает все подключения.
        """

        if self.client:
            self.client.close()
        if self.doc_fetcher:
            self.doc_fetcher.close()
        print("All connections closed")
