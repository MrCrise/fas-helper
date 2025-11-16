from transformers import AutoTokenizer
from chunkers.sentence_chunker import SentenceChunker
from constants import TOKENIZER_NAME
from text import *
from FlagEmbedding import BGEM3FlagModel
from constants import EMBEDDING_MODEL_NAME

model = BGEM3FlagModel(EMBEDDING_MODEL_NAME, use_fp16=True)

tokenizer = AutoTokenizer.from_pretrained(
    TOKENIZER_NAME, trust_remote_code=True)

text = document
chunker = SentenceChunker(tokenizer)

chunks = chunker.chunk(text)
print("Чанков:", len(chunks))
for i in range(len(chunks)):
    print(f"Токенов в {i}-ом:", chunks[i]["token_count"])
print()

chunk_texts = [chunk.get("text") for chunk in chunks]
chunk_embeddings = model.encode(chunk_texts)
print(chunk_embeddings)
