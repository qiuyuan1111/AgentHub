import json
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent

KNOWLEDGE_DIR = BASE_DIR / "data" / "knowledge"

STORAGE_DIR = BASE_DIR / "storage"

INDEX_PATH = STORAGE_DIR / "knowledge.index"

CHUNKS_PATH = STORAGE_DIR / "chunks.json"

embedding_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

def load_document() -> list[dict]:
    document = []

    # 把 build_index.py 从单文件读取升级成多文件读取
    for file_path in KNOWLEDGE_DIR.iterdir():

        if file_path.suffix not in [".txt", ".md"]:
            continue

        text = file_path.read_text(encoding="utf-8")

        document.append(
            {
                "text": text,
                "source": file_path.name
            }
        )

    return document

def split_document(
    text: str,
    source: str
) -> list[dict]:

    chunks = []

    chunk_id = 0

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Chunk 也开始带 Metadata
        chunks.append(
            {
                "text": paragraph,
                "source": source,
                "chunk_id": chunk_id
            }
        )

        chunk_id += 1

    return chunks

def build_index():

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    documents = load_document()

    chunks = []

    # 把所有文档 Chunk 合并
    for document in documents:

        document_chunks = split_document(
            text=document["text"],
            source=document["source"]
        )

        chunks.extend(document_chunks)

    chunk_texts = []

    for chunk in chunks:
        chunk_texts.append(chunk["text"])

    embeddings = embedding_model.encode(
        chunk_texts,
        normalize_embeddings=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    # 取得向量维度
    dimension = embeddings.shape[1]

    # 创建 FAISS 索引仓库
    index = faiss.IndexFlatIP(dimension)

    # 放入向量
    index.add(embeddings)

    # print("索引中的向量数量:", index.ntotal)

    # 把 FAISS 保存到硬盘
    faiss.write_index(
        index,
        str(INDEX_PATH)  # 因为 INDEX_PATH 原本是Path对象
    )

    # 保存 Chunk
    with CHUNKS_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("知识库索引构建完成")
    print("Chunk数量:", len(chunks))
    print("Embedding维度:", dimension)
    print("FAISS向量数量:", index.ntotal)
    print("索引保存位置:", INDEX_PATH)

if __name__ == "__main__":
    build_index()