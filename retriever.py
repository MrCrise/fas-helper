import asyncio
from typing import List, Dict, Any
from qdrant_client import AsyncQdrantClient, models
from FlagEmbedding import BGEM3FlagModel
from constants import QDRANT_COLLECTION_NAME
from document_fetcher import AsyncDocumentFetcher


class AsyncRetriever:
    def __init__(self,
                 qdrant_client: AsyncQdrantClient,
                 model: BGEM3FlagModel,
                 doc_fetcher: AsyncDocumentFetcher):
        self.client = qdrant_client
        self.model = model
        self.doc_fetcher = doc_fetcher
        self.collection_name = QDRANT_COLLECTION_NAME

    def _convert_sparse_vector(self, sparse_weights: dict) -> models.SparseVector:
        """
        Конвертирует sparse веса, полученные из модели BGE
        в формат, поддерживаемый Qdrant.
        """

        sparse_indices = []
        sparse_values = []

        for key, value in sparse_weights.items():
            if isinstance(key, str):
                if key.isdigit():
                    key = int(key)
                else:
                    continue
            if float(value) > 0:
                sparse_indices.append(key)
                sparse_values.append(float(value))

        return models.SparseVector(
            indices=sparse_indices,
            values=sparse_values
        )

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Ищет релевантные документы по запросу.
        """

        loop = asyncio.get_running_loop()
        query_embedding = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                query,
                return_dense=True,
                return_sparse=True,
                return_colbert_vecs=True
            )
        )

        dense_vec = query_embedding["dense_vecs"].tolist()
        sparse_vec = self._convert_sparse_vector(query_embedding["lexical_weights"])
        colbert_vecs = [vec.tolist() for vec in query_embedding["colbert_vecs"]]

        prefetch_limit = limit * 3

        search_result = await self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_vec,
                    using="dense",
                    limit=prefetch_limit
                ),
                models.Prefetch(
                    query=sparse_vec,
                    using="sparse",
                    limit=prefetch_limit
                )
            ],
            query=colbert_vecs,
            using="colbert",
            limit=prefetch_limit,
            with_payload=True
        )

        unique_docs: Dict[str, Dict] = {}

        for point in search_result.points:
            payload = point.payload
            doc_id = payload.get("doc_id")

            if doc_id in unique_docs:
                if point.score > unique_docs[doc_id]["score"]:
                    unique_docs[doc_id]["score"] = point.score
                    unique_docs[doc_id]["best_chunk"] = payload.get("text", "")
            else:
                unique_docs[doc_id] = {
                    "doc_id": doc_id,
                    "score": point.score,
                    # "title": payload.get("title", ""),
                    "best_chunk": payload.get("text", ""),
                    "full_text": None
                }

            if len(unique_docs) >= limit:
                break

        sorted_results = sorted(
            unique_docs.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:limit]

        doc_ids_to_fetch = [doc["doc_id"] for doc in sorted_results]

        full_texts_map = await self.doc_fetcher.get_texts_by_ids(doc_ids_to_fetch)

        for result in sorted_results:
            result["full_text"] = full_texts_map.get(result["doc_id"])

        return sorted_results
