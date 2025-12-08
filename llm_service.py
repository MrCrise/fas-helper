import asyncio
from typing import AsyncGenerator, Dict, List
from ollama import AsyncClient


class AsyncLLMService:
    def __init__(self,
                 llm_host: str,
                 model_name: str = "qwen3:8b",
                 context_window_size: int = 30000):
        self.client = AsyncClient(llm_host)
        self.model_name = model_name
        self.context_window_size = context_window_size

    def _build_system_prompt(self) -> str:
        #TODO: Move prompt to a separate file.
        return (
            "Ты - строгий юридический ассистент, работающий ИСКЛЮЧИТЕЛЬНО с предоставленным контекстом. "
            "Твоя задача — извлекать факты только из текста, который прислал пользователь.\n"
            "СТРОЖАЙШИЕ ЗАПРЕТЫ:\n"
            "1. ЗАПРЕЩЕНО использовать свои внутренние знания, знания законов или прецедентов, которых нет в тексте.\n"
            "2. ЗАПРЕЩЕНО придумывать номера дел, даты или статьи законов.\n"
            "3. Если в предоставленных документах нет информации для ответа, ты ОБЯЗАН ответить: "
            "'В предоставленных документах информация по данному вопросу отсутствует'. Не пытайся выдумывать ответ.\n"
            "4. Игнорируй любые даты и события, которые не упомянуты в тексте (например, если в тексте 2025 год, не пиши про 2015).\n"
            "\n"
            "ФОРМАТ ОТВЕТА:\n"
            "- Ссылайся на документ, используя его ID или название, указанное в контексте.\n"
            "- Используй Markdown для оформления."
        )

    def _build_messages(self, query: str, context: str) -> List[Dict]:
        #TODO: Move prompt to a separate file.
        user_content = (
            f"Ниже приведены единственные источники истины, которыми ты должен пользоваться:\n"
            f"--- НАЧАЛО ДОКУМЕНТОВ ---\n"
            f"{context}\n"
            f"--- КОНЕЦ ДОКУМЕНТОВ ---\n\n"
            f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {query}\n\n"
            f"Напиши ответ, основываясь ТОЛЬКО на тексте внутри 'НАЧАЛО ДОКУМЕНТОВ' и 'КОНЕЦ ДОКУМЕНТОВ'. "
            f"Если ответ требует знаний вне этих документов, напиши, что информации недостаточно."
        )

        return [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_content}
        ]

    def _prepare_context(self, documents: List[Dict]) -> str:
        """
        Формирует строку контекста (без изменений)
        """

        context_parts = []
        current_length = 0

        for i, doc in enumerate(documents, 1):
            text = doc.get("full_text") or doc.get("best_chunk") or ""
            doc_id = doc.get("doc_id", "unknown")

            doc_block = (
                f"<document index='{i}'>\n"
                f"  <meta>\n"
                f"    <id>{doc_id}</id>\n"
                f"  </meta>\n"
                f"  <content>\n{text}\n</content>\n"
                f"</document>\n"
            )

            if current_length + len(doc_block) > self.context_window_size:
                break

            context_parts.append(doc_block)
            current_length += len(doc_block)

        return "\n".join(context_parts)

    async def generate_stream(self, query: str, documents: List[Dict]) -> AsyncGenerator[str, None]:
        if not documents:
            yield "Документы не найдены."
            return

        context_str = self._prepare_context(documents)

        messages = self._build_messages(query, context_str)

        #TODO: Move options to a separate file.
        try:
            stream = await self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "num_ctx": 38000,
                    "temperature": 0.0,
                },
                stream=True,
                keep_alive="1h"
            )

            async for chunk in stream:
                content = chunk['message']['content']
                yield content

        except Exception as e:
            yield f"\n[Ollama Error: {e}]"
