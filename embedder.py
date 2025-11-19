from collections import defaultdict
from typing import Any, Dict, List
from qdrant_client import QdrantClient, models
from FlagEmbedding import BGEM3FlagModel
from tqdm import tqdm
from transformers import AutoTokenizer


class Embedder:
    def __init__(self, client: QdrantClient,
                 model: BGEM3FlagModel,
                 tokenizer: AutoTokenizer):
        self.client: QdrantClient = client
        self.model: BGEM3FlagModel = model
        self.tokenizer: AutoTokenizer = tokenizer

    def create_qdrant_collection(self,
                                 collection_name: str = "legal_rag") -> None:
        """
        Создаёт коллекцию в Qdrant с нужной конфигурацией векторов.
        """

        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=1024,
                        distance=models.Distance.COSINE
                    ),
                    "colbert": models.VectorParams(
                        size=1024,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        ),
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(
                            on_disk=True
                        )
                    )
                },
            )

            print(f"Коллекция '{collection_name}' создана")

    def generate_embedding(self, text: str) -> Dict[str, Any]:
        return self.model.encode(text,
                                 return_dense=True,
                                 return_sparse=True,
                                 return_colbert_vecs=True)

    def generate_chunk_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Генерирует векторные представления для всех переданных чанков.
        """

        chunk_embeddings = []

        for chunk in tqdm(chunks, desc="Генерация эмбеддингов: "):
            chunk_text = chunk.get("text")

            model_output = self.generate_embedding(chunk_text)

            chunk_embedding = {
                "chunk": chunk,
                "dense_vector": model_output.get("dense_vecs"),
                "sparse_weights": model_output.get("lexical_weights"),
                "colbert_vectors": model_output.get("colbert_vecs")
            }

            chunk_embeddings.append(chunk_embedding)

        print(f"Сгенерировано {len(chunk_embeddings)} эмбеддингов")

        return chunk_embeddings

    def convert_sparse_vector(self, sparse_weigths: defaultdict) -> models.SparseVector:
        """
        Конвертирует sparse веса, полученные из модели BGE
        в формат, поддерживаемый Qdrant.
        """

        sparse_indices = []
        sparse_values = []

        for key, value in sparse_weigths.items():
            if float(value) > 1:
                if isinstance(key, str):
                    if key.isdigit():
                        key = int(key)
                    else:
                        continue

                sparse_indices.append(key)
                sparse_values.append(float(value))

        return models.SparseVector(
            indices=sparse_indices,
            values=sparse_values
        )

    def insert_to_qdrant(self, embeddings: List[Dict[str, Any]],
                         collection_name: str = "legal_rag") -> None:
        """
        Загружает переданные эмбеддинги в коллекцию Qdrant.
        """

        for embedding in tqdm(embeddings, desc="Загрузка в Qdrant: "):
            chunk = embedding.get("chunk")
            dense_vector = embedding.get("dense_vector")
            sparse_weights = embedding.get("sparse_weights")
            colbert_vectors = embedding.get("colbert_vectors")

            converted_sparse = self.convert_sparse_vector(sparse_weights)

            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=chunk.get("index"),  # TODO: Change id getting logic to get unique ids for points of different documents.
                        payload=chunk,
                        vector={
                            "dense": dense_vector,
                            "sparse": converted_sparse,
                            "colbert": colbert_vectors
                        }
                    )
                ]
            )

        print(f"Загружено {len(embeddings)} эмбеддингов в коллекцию {collection_name}")
