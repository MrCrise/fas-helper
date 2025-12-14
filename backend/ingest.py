import os
from transformers import AutoTokenizer
from chunkers.sentence_chunker import SentenceChunker
from constants import TOKENIZER_NAME
from FlagEmbedding import BGEM3FlagModel
from qdrant_client import QdrantClient
from constants import EMBEDDING_MODEL
from embedder import Embedder

from database import count_cases, clear_all_tables, load_database_url, create_db_engine, create_metadata
from parser import parse_data, create_chrome_driver, create_firefox_driver

if __name__ == '__main__':
    try:
        model = BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=True,
                               device='cuda')

        tokenizer = AutoTokenizer.from_pretrained(
            TOKENIZER_NAME, trust_remote_code=True)
        

        qdrant_host = os.getenv("QDRANT_HOST")
        qdrant_port = int(os.getenv("QDRANT_PORT"))
        client = QdrantClient(
            host=qdrant_host,
            port=qdrant_port,
            prefer_grpc=True,
            timeout=100
        )

        chunker = SentenceChunker(tokenizer)

        embedder = Embedder(client=client, model=model, tokenizer=tokenizer)

        driver = create_chrome_driver()

        DATABASE_URL = load_database_url()

        engine = create_db_engine(DATABASE_URL, logging=False)

        metadata = create_metadata(engine)

        # clear_all_tables(engine, metadata)
        parse_data(driver, chunker, embedder, engine, metadata, start_page=50, last_page=1)

        print('-' * 50)
        print(f'Number of cases in the db: {count_cases(engine=engine, metadata=metadata)}')

    finally:
        driver.quit()
