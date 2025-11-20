from transformers import AutoTokenizer
from chunkers.sentence_chunker import SentenceChunker
from constants import TOKENIZER_NAME
from text import *
from FlagEmbedding import BGEM3FlagModel
from qdrant_client import QdrantClient
from constants import EMBEDDING_MODEL
from embedder import Embedder

from database import count_cases, clear_all_tables
from parser import parse_data, create_chrome_driver, create_firefox_driver

if __name__ == '__main__':  
    try:
        model = BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=True,
                            device='cuda')

        tokenizer = AutoTokenizer.from_pretrained(
            TOKENIZER_NAME, trust_remote_code=True)

        client = QdrantClient(host="localhost", port=6333)

        chunker = SentenceChunker(tokenizer)
        
        embedder = Embedder(client=client, model=model, tokenizer=tokenizer)
        
        driver = create_chrome_driver()
        
        clear_all_tables()
        parse_data(driver, chunker, embedder, start_page = 2)
        
        print('-' * 50)
        print(f'Number of cases in the db: {count_cases()}')

    finally:
        driver.quit()
