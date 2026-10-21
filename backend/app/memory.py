from threading import RLock
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models


class Memory:
    def __init__(self, settings, provider, store):
        self.provider, self.store = provider, store
        self.lock = RLock()
        self.client = (
            QdrantClient(url=settings.qdrant_url, timeout=10)
            if settings.qdrant_url
            else QdrantClient(path=str(settings.data_dir / "vectors"))
        )
        self.collection = provider.embedding_namespace
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection, vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
            )

    def ingest(self, project_id, doc_id, title, content):
        chunks = [content[i : i + 1800] for i in range(0, len(content), 1500)]
        points = []
        for index, chunk in enumerate(chunks):
            citation = f"{doc_id}:{index + 1}"
            vector = self.provider.embed(title + "\n" + chunk)
            points.append(
                models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, citation)),
                    vector=vector,
                    payload=dict(project_id=project_id, document_id=doc_id, citation=citation, title=title, text=chunk),
                )
            )
        with self.lock:
            self.client.upsert(collection_name=self.collection, points=points, wait=True)
        return len(points)

    def search(self, project_id, query, limit=4):
        if not self.store.knowledge(project_id):
            return []
        vector = self.provider.embed(query, query=True)
        with self.lock:
            result = self.client.query_points(
                collection_name=self.collection,
                query=vector,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="project_id", match=models.MatchValue(value=project_id))]
                ),
                limit=limit,
                score_threshold=0.08,
            )
        # SQL documents are authoritative: ignore orphaned vector points.
        valid = {doc["id"] for doc in self.store.knowledge(project_id)}
        return [
            dict(point.payload) | {"score": round(point.score, 4)}
            for point in result.points
            if point.payload["document_id"] in valid
        ]

    def close(self):
        self.client.close()
