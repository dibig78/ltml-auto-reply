"""ChromaDB 벡터 검색."""
def search_docs(query: str, top_k: int = 5) -> list[dict]:
    try:
        import chromadb
        from src.config import CHROMA_DIR
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        col = client.get_collection("ltml_knowledge")
        res = col.query(query_texts=[query], n_results=top_k)
        docs = []
        if res and res["documents"]:
            for i, doc in enumerate(res["documents"][0]):
                meta = res["metadatas"][0][i] if res["metadatas"] else {}
                docs.append({"text": doc, "source": meta.get("source",""), "score": 1 - (res["distances"][0][i] if res["distances"] else 0)})
        return docs
    except Exception as e:
        print(f"[WARN] RAG 검색 실패: {e}")
        return []
