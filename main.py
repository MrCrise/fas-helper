from transformers import AutoTokenizer
from chunkers.sentence_chunker import SentenceChunker
from chunkers.token_chunker import TokenChunker
from text import *


TOKENIZER_NAME = "Qwen/Qwen3-8B"
tokenizer = AutoTokenizer.from_pretrained(
    TOKENIZER_NAME, trust_remote_code=True)


text = document_3
chunker = SentenceChunker(tokenizer)
# norm_text = chunker.normalize_text(text)
chunks = chunker.chunk(text)
print("Чанков:", len(chunks))
for i in range(len(chunks)):
    print(f"Токенов в {i}-ом:", chunks[i]["token_count"])
print()
# print("Чанк:\n", chunks[0]["text"])
# print()
# print("Чанк:\n", chunks[1]["text"])
# print()
# print("Чанк:\n", chunks[2]["text"])
for i in range(len(chunks)):
    print(f"Чанк {i} ({chunks[i]["start_char"]}:{chunks[i]["end_char"]}):", chunks[i]["text"])
    print()
    # print(f"Исходный текст ({chunks[i]["start_char"]}:{chunks[i]["end_char"]}):", norm_text[chunks[i]["start_char"]:chunks[i]["end_char"]])
    # print()
    # print()
    # print()

