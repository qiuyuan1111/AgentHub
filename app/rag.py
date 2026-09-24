from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

# 找到项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = BASE_DIR / "data" / "company_policy.txt"

# 加载 Embedding 模型
embedding_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

def load_document():
    text = DOCUMENT_PATH.read_text(
        encoding="utf-8"
    )

    return text

def split_document(text: str) -> list[str]:
    chunks = []

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()

        if paragraph:
            chunks.append(paragraph)
    return chunks

document_text = load_document()

chunks = split_document(document_text)

chunks_embedding = embedding_model.encode(
    chunks,
    normalize_embeddings=True
)

def search_knowledge_base(
        query: str,
        top_k: int = 3,
        min_score: float = 0.65
) -> list[dict]:

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True
    )

    scores = np.dot(
        chunks_embedding,
        query_embedding
    )

    sorted_indices = np.argsort(scores)[::-1]

    results = []

    for index in sorted_indices:
        score = float(scores[index])

        if score < min_score:
            break
        results.append(
            {
                "text": chunks[index],
                "score": score
            }
        )

        if len(results) >= top_k:
            break

    return results