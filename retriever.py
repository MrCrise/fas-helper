from typing import List, Dict, Any
from qdrant_client import QdrantClient, models
from FlagEmbedding import BGEM3FlagModel
from constants import EMBEDDER_VER


class Retriever:
    def __init__(self, client: QdrantClient, model: BGEM3FlagModel):
        self.client = client
        self.model = model
        self.version = EMBEDDER_VER

    def search_qdrant(self,
                      query: str,
                      top_k: int = 15,
                      collection_name: str = "legal_rag") -> List[Dict[str, Any]]:
        """
        Выполняет гибридный поиск (Dense + Sparse) в Qdrant.
        """
        # Генерация векторов запроса. colbert выключен для ускорения retrieval-этапа.
        query_outputs = self.model.encode([query],
                                          return_dense=True,
                                          return_sparse=True,
                                          return_colbert_vecs=False)

        query_dense = query_outputs['dense_vecs'][0]
        query_sparse = query_outputs['lexical_weights'][0]

        search_requests = [
            models.QueryRequest(
                query=query_dense.tolist(),
                using="dense",
                limit=top_k,
                with_payload=True,
            ),
            models.QueryRequest(
                query=self.convert_sparse_vector(query_sparse),
                using="sparse",
                limit=top_k,
                with_payload=True
            )
        ]

        try:
            search_results_batch = self.client.query_batch_points(
                collection_name=collection_name,
                requests=search_requests
            )

            reranker_input = []
            seen_point_ids = set()

            # Объединяем результаты двух запросов (Dense и Sparse) с дедупликацией
            for request_result in search_results_batch:
                for hit in request_result.points:
                    if not hit.payload:
                        continue

                    # Дедупликация по ID точки в векторе
                    if hit.id in seen_point_ids:
                        continue
                    seen_point_ids.add(hit.id)

                    chunk_text = hit.payload.get('text')
                    if not chunk_text:
                        continue

                    reranker_input.append({
                        "text": chunk_text,
                        "retrieval_score": hit.score,
                        "doc_id": hit.payload.get('doc_id')
                    })

            return reranker_input

        except Exception as e:
            print(f"Qdrant search error: {e}")
            return []

    @staticmethod
    def convert_sparse_vector(sparse_weights: dict) -> models.SparseVector:
        """Конвертация весов BGE-M3 в формат Qdrant."""
        indices = []
        values = []

        for key, value in sparse_weights.items():
            if float(value) <= 0:
                continue

            # Обработка ключей, если они пришли как строки цифр
            if isinstance(key, str):
                if key.isdigit():
                    key = int(key)
                else:
                    continue

            indices.append(key)
            values.append(float(value))

        return models.SparseVector(indices=indices, values=values)