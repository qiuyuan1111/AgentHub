import json
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent

DOCUMENT_PATH = BASE_DIR / "data" / "company_policy.txt"

STORAGE_DIR = BASE_DIR / "storage"

INDEX_PATH = STORAGE_DIR / "knowledge.index"

CHUNKS_PATH = STORAGE_DIR / "chunks.json"

embedding_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

def load_document() -> str:
    return DOCUMENT_PATH.read_text(
        encoding="utf-8"
    )

def split_document(text: str) -> list[str]:
    chunks = []

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if paragraph:
            chunks.append(paragraph)

    return chunks

def build_index():

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    document_text = load_document()

    chunks = split_document(document_text)

    embeddings = embedding_model.encode(
        chunks,
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