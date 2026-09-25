from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

# 找到项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = BASE_DIR / "data" / "company_policy.txt"

# 加载 Embedding 模型
embedding_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

reranker_model = CrossEncoder(
    "BAAI/bge-reranker-base"
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

def retrieve_candidates(
        query: str,
        top_k: int = 5,
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

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 3,
    min_rerank_score: float = 0.5
)->list[dict]:

    if not candidates:
        return []

    pairs = []

    for candidate in candidates:
        pairs.append(
            [query,candidate["text"]]
        )

        rerank_scores = reranker_model.predict(pairs)

        reranked_results = []

    for candidate, score in zip(
            candidates,
            rerank_scores
    ):
        reranked_results.append(
            {
                "text": candidate["text"],
                "retrieval_score": candidate["score"],
                "rerank_score": float(score)
            }
        )

    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    filtered_results = []

    for item in reranked_results:
        if item["rerank_score"] < min_rerank_score:
            break

        filtered_results.append(item)

        if len(filtered_results) >= top_k:
            break

    return filtered_results

def search_knowledge_base(
        query: str,
        top_k: int = 3
) -> list[dict]:
    candidates = retrieve_candidates(
        query=query,
        top_k=5,
        min_score=0.5
    )

    results = rerank(
        query,
        candidates,
        top_k=top_k
    )

    return results