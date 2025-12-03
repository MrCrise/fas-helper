import asyncio
from typing import AsyncGenerator, Dict, List
from ollama import AsyncClient


class AsyncLLMService:
    def __init__(self,
                 llm_host: str,
                 model_name: str = "qwen3:8b",
                 context_window_size: int = 20000):
        self.client = AsyncClient(llm_host)
        self.model_name = model_name
        self.context_window_size = context_window_size

    def _build_system_prompt(self) -> str:
        # return (
        #     "Ты - профессиональный юридический помощник Федеральной антимонопольной службы. "
        #     "Твоя задача - отвечать на вопросы пользователя, основываясь ИСКЛЮЧИТЕЛЬНО на предоставленных документах.\n"
        #     "Правила:\n"
        #     "1. Не используй собственные знания, если их нет в контексте.\n"
        #     "2. Если в документах нет ответа, так и скажи: 'К сожалению, в базе данных нет информации по данному вопросу'.\n"
        #     "3. Ссылайся на документы, указывая их названия или номера дел, когда приводишь факты.\n"
        #     "4. Не привязывайся к рассмотрению конкретных дел, если тебя не просили об обратном."
        #     "5. Ответ должен быть полным, юридически грамотным, но понятным.\n"
        #     "6. Форматируй ответ в Markdown."
        # )
        return (
            "Ты — старший юрист-аналитик ФАС России. "
            "Твоя задача — дать обобщенный правовой ответ на вопрос пользователя, проанализировав предоставленную судебную практику и решения. "
            "\n\n"
            "ПРАВИЛА ОТВЕТА:\n"
            "1. НЕ пересказывай содержимое одного документа. Твоя цель — выявить общую правовую позицию или тенденцию.\n"
            "2. Сначала сформулируй прямой ответ на вопрос, затем приводи примеры из документов.\n"
            "3. Если в документах описаны разные ситуации, сгруппируй их (например: «Суды признают нарушением А, Б и В...»).\n"
            "4. Используй предоставленные документы как ДОКАЗАТЕЛЬСТВА. Ссылайся на них в скобках или сносках (например: «...что подтверждается решением №...»).\n"
            "5. Если документы противоречат друг другу, укажи это.\n"
            "6. Не придумывай нормы права, которых нет в контексте."
        )

    def _build_messages(self, query: str, context: str) -> List[Dict]:
        user_content = (
            f"ВОПРОС: {query}\n\n"
            f"МАТЕРИАЛЫ ДЛЯ АНАЛИЗА (судебная практика и решения):\n"
            f"{context}\n\n"
            f"ИНСТРУКЦИЯ:\n"
            f"1. Проанализируй все предоставленные документы.\n"
            f"2. Ответь на вопрос: какие условия считаются дискриминационными или нарушающими закон, исходя из этих текстов?\n"
            f"3. Подтверди свои выводы конкретными примерами из текстов (номера дел, даты).\n"
            f"4. Структурируй ответ: тезис -> обоснование -> пример из практики."
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

            doc_block = f"<document id='{doc_id}'>\n{text}\n</document>\n"

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

        try:
            stream = await self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "num_ctx": 16384
                },
                stream=True,
            )

            async for chunk in stream:
                content = chunk['message']['content']
                yield content

        except Exception as e:
            yield f"\n[Ollama Error: {e}]"
