"""TDS/MSDS PDF → ChromaDB 벡터 임베딩."""
import chromadb
from pathlib import Path
from src.config import KNOWLEDGE_DIR, CHROMA_DIR

def extract_pdf(path: Path) -> str:
    try:
        import fitz
        doc = fitz.open(str(path))
        return "\n".join(p.get_text() for p in doc).strip()
    except: return ""

def chunk(text: str, size=1000, overlap=200) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        c = text[start:start+size].strip()
        if c: chunks.append(c)
        start += size - overlap
    return chunks

def ingest():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try: client.delete_collection("ltml_knowledge")
    except: pass
    col = client.create_collection("ltml_knowledge")
    docs, metas, ids, n = [], [], [], 0
    for pdf in KNOWLEDGE_DIR.glob("*.pdf"):
        print(f"처리: {pdf.name}")
        text = extract_pdf(pdf)
        if not text: continue
        for i, c in enumerate(chunk(text)):
            docs.append(c); metas.append({"source": pdf.name, "chunk": i}); ids.append(f"d_{n}"); n += 1
    # FAQ
    import json
    faq_file = Path("data/faq.json")
    if faq_file.exists():
        for f in json.loads(faq_file.read_text()):
            docs.append(f"질문: {f['question']}\n답변: {f['answer']}")
            metas.append({"source":"faq.json","type":"faq"}); ids.append(f"d_{n}"); n += 1
    if docs:
        for i in range(0, len(docs), 100):
            col.add(documents=docs[i:i+100], metadatas=metas[i:i+100], ids=ids[i:i+100])
    print(f"✅ {n}건 임베딩 완료")

if __name__ == "__main__":
    ingest()
