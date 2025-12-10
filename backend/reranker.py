from typing import List, Dict, Any

class Reranker:
    def __init__(self, model: Any):
        """
        :param model: Загруженная модель (FlagReranker или FlagLLMReranker).
        """
        self.model = model

    def rerank(self,
               query: str,
               retrieved_chunks: List[Dict[str, Any]],
               top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Переранжирует список кандидатов на основе семантической близости к запросу.
        """
        if not retrieved_chunks:
            return []

        # Формируем пары [query, document] для Cross-Encoder
        pairs = [[query, chunk['text']] for chunk in retrieved_chunks]

        try:
            scores = self.model.compute_score(pairs)

            # Обработка вывода layerwise моделей (MiniCPM), которые возвращают список списков
            if isinstance(scores, list) and scores and isinstance(scores[0], list):
                scores = [s[-1] for s in scores]

        except Exception as e:
            print(f"Error during reranking: {e}")
            # В случае ошибки возвращаем исходный порядок, обрезанный до top_n
            return retrieved_chunks[:top_n]

        # Присваиваем скоры
        for i, score in enumerate(scores):
            retrieved_chunks[i]['rerank_score'] = float(score)

        # Сортировка по убыванию релевантности
        reranked_results = sorted(
            retrieved_chunks,
            key=lambda x: x['rerank_score'],
            reverse=True
        )

        return reranked_results[:top_n]