from typing import Any, Dict, List
from chunkers.base_chunker import BaseChunker
import re


class SentenceChunker(BaseChunker):
    RUSSIAN_ABBREVS = ["г", "гг", "ул", "д", "стр", "ст", "п", "ч", "т", "пп", "см", "рис", "т.д", "и др",
                       "пр", "ст", "ч", "п", "с", "инд", "ФЗ", "РФ", "КоАП", "ИП", "ООО", "ЗАО", "ОАО"]
    DOT_MASK = "‹DOT›"

    def __init__(self, tokenizer):
        super().__init__(tokenizer)

        clean = [re.escape(a.rstrip('.')) for a in self.RUSSIAN_ABBREVS]
        self._abbrev_re = re.compile(
            r"\b(?:" + "|".join(clean) + r")\.(?=\s|$)", flags=re.IGNORECASE)
        self._initials_re = re.compile(
            r"\b(?:[A-ZА-ЯЁ]\.){1,3}(?=\s|[A-ZА-ЯЁ])")

    def get_token_count(self, text: str) -> int:
        return len(self.tokenize(text))

    def _mask_abbr(self, text: str) -> str:
        text = self._abbrev_re.sub(
            lambda m: m.group(0)[:-1] + self.DOT_MASK, text)
        text = self._initials_re.sub(lambda m: m.group(
            0).replace('.', self.DOT_MASK), text)
        return text

    def _unmask_abbr(self, text: str) -> str:
        return text.replace(self.DOT_MASK, ".")

    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Разбивает текст на фрагменты по предложениям.
        """

        masked_text = self._mask_abbr(text)

        sentence_re = re.compile(
            r'(?P<end>[\.\!\?\…]{1,3}["\)\]\»\']{0,1})(?=\s+|$)', flags=re.UNICODE)

        sentences = []
        masked_pos = 0
        orig_pos = 0

        for m in sentence_re.finditer(masked_text):
            end_of_sentence = m.end(1)
            sent_masked = masked_text[masked_pos:end_of_sentence].strip()
            if sent_masked:
                sent = self._unmask_abbr(sent_masked)
                start = text.find(sent, orig_pos)
                if start == -1:
                    start = text.find(sent)
                if start == -1:
                    start = orig_pos
                end = start + len(sent)
                sentences.append({"text": sent, "start": start, "end": end})
                orig_pos = end

            masked_pos = m.end()

        if masked_pos < len(masked_text):
            tail_masked = masked_text[masked_pos:].strip()
            if tail_masked:
                tail = self._unmask_abbr(tail_masked)
                start = text.find(tail, orig_pos)
                if start == -1:
                    start = text.find(tail)
                if start == -1:
                    start = orig_pos
                end = start + len(tail)
                sentences.append({"text": tail, "start": start, "end": end})

        return sentences

    def _sliding_window_chunk(self, text: str,
                              chunk_size: int = 600,
                              overlap: int = 90) -> List[Dict[str, Any]]:

        sentences = self._split_by_sentences(text)

        token_counts = [self.get_token_count(s["text"]) for s in sentences]
        min_tail_tokens = max(int(0.25*chunk_size), 150)
        n = len(sentences)

        chunks = []
        i = 0
        chunk_num = 0
        while i < n:
            cur_tokens = 0
            j = i
            while j < n and (cur_tokens + token_counts[j] <= chunk_size or j == i):
                cur_tokens += token_counts[j]
                j += 1

            start_char = sentences[i]["start"]
            end_char = sentences[j - 1]["end"]

            chunk_text = text[start_char:end_char]
            chunk_tokens = self.get_token_count(chunk_text)

            chunks.append({"index": chunk_num,
                           "text": chunk_text,
                           "start_char": start_char,
                           "end_char": end_char,
                           "token_count": chunk_tokens})

            chunk_num += 1

            if j >= n:
                break
            if overlap <= 0:
                i = j
            else:
                back = j - 1
                accum = 0
                while back >= i and accum < overlap:
                    accum += token_counts[back]
                    back -= 1
                next_i = max(i + 1, back + 1)
                i = next_i

        while len(chunks) > 1 and chunks[-1]["token_count"] < min_tail_tokens:
            tail = chunks.pop()
            prev = chunks[-1]
            merged_start = prev["start_char"]
            merged_end = tail["end_char"]
            merged_text = text[merged_start:merged_end]
            merged_tokens = self.get_token_count(merged_text)

            prev["text"] = merged_text
            prev["start_char"] = merged_start
            prev["end_char"] = merged_end
            prev["token_count"] = merged_tokens

        return chunks

    def chunk(self, text: str,
              chunk_size: int = 800,
              overlap: int = 100) -> List[Dict[str, Any]]:

        text = self.normalize_text(text)
        chunks = self._sliding_window_chunk(text, chunk_size, overlap)

        return chunks
