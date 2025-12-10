from chunkers.base_chunker import BaseChunker


class TokenChunker(BaseChunker):
    def __init__(self, tokenizer):
        super().__init__(tokenizer)

    def chunk_tokens_by_size(self, text: str, chunk_size: int = 600,
                             overlap: int = 100):
        """
        Разбивает текст на чанки по фиксированному
        количеству токенов с перекрытием.
        """

        tokens = self.tokenize(text)
        chunks = []
        i = 0
        n = len(tokens)
        step = chunk_size - overlap

        if step <= 0:
            raise ValueError("Chunk size must be > overlap")

        while i < n:
            end = min(i + chunk_size, n)
            chunk_ids = tokens[i:end]
            chunks.append({
                "tokens": chunk_ids,
                "text": self.detokenize(chunk_ids),
                "start_token": i,
                "end_token": end
            })
            i += step

        return chunks
