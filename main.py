from transformers import AutoTokenizer
from chunkers.sentence_chunker import SentenceChunker
from constants import TOKENIZER_NAME
from text import *
from FlagEmbedding import BGEM3FlagModel
from qdrant_client import QdrantClient
from constants import EMBEDDING_MODEL
from embedder import Embedder

model = BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=True,
                       device='cuda')

tokenizer = AutoTokenizer.from_pretrained(
    TOKENIZER_NAME, trust_remote_code=True)

client = QdrantClient(host="localhost", port=6333)

text = document
chunker = SentenceChunker(tokenizer)

chunks = chunker.chunk(text)
print("Чанков:", len(chunks))
for i in range(len(chunks)):
    print(f"Токенов в {i}-ом:", chunks[i]["token_count"])
print()

embedder = Embedder(client=client, model=model, tokenizer=tokenizer)

embedder.create_qdrant_collection()
embeddings = embedder.generate_chunk_embeddings(chunks)

embedder.insert_to_qdrant(embeddings)
