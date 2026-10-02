import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

import time

from app.config import (
    RETRIEVAL_TOP_N,
    RETRIEVAL_MIN_SCORE,
    RERANK_TOP_K,
    RERANK_MIN_SCORE
)

# 找到项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = BASE_DIR / "data" / "company_policy.txt"
STORAGE_DIR = BASE_DIR / "storage"
INDEX_PATH = STORAGE_DIR / "knowledge.index"
CHUNKS_PATH = STORAGE_DIR / "chunks.json"


import torch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 加载 Embedding 模型
embedding_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

reranker_model = CrossEncoder(
    "BAAI/bge-reranker-base"
)

def warmup_rag_models():

    print("正在进行 RAG 模型预热...")

    # 让 Embedding 模型先假跑一次
    embedding_model.encode(
        ["模型预热"],
        normalize_embeddings=True
    )

    # 让 Reranker 先假跑一次
    reranker_model.predict(
        [
            [
                "模型预热",
                "这是一段用于模型预热的文本。"
            ]
        ]
    )

    print("RAG 模型预热完成")

warmup_rag_models()

print("Embedding device:", embedding_model.device)

print(
    "Reranker device:",
    next(reranker_model.model.parameters()).device
)

# 从硬盘加载 FAISS
index = faiss.read_index(
    str(INDEX_PATH)
)

# 加载 chunks.json
with CHUNKS_PATH.open(
    "r",
    encoding="utf-8"
)as file:
    chunks = json.load(file)

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



def retrieve_candidates(
        query: str,
        top_n: int = RETRIEVAL_TOP_N,
        min_score: float = RETRIEVAL_MIN_SCORE
) -> list[dict]:

    retrieve_start = time.perf_counter()

    # =========================
    # 1. Query Embedding
    # =========================

    embedding_start = time.perf_counter()

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    embedding_time = time.perf_counter() - embedding_start

    # =========================
    # 2. FAISS Search
    # =========================
    faiss_start = time.perf_counter()

    search_k = min(
        top_n,
        index.ntotal
    )

    # 自动返回降序的分数
    scores, indices = index.search(
        query_embedding,
        search_k
    )

    faiss_time = time.perf_counter() - faiss_start

    candidates = []

    for score, chunk_index in zip(scores[0], indices[0]):
        score = float(score)
        chunk_index = int(chunk_index)

        if score < min_score:
            break

        chunk = chunks[chunk_index]
        candidates.append(
            {
                "text": chunk["text"],
                "source": chunk["source"],
                "page": chunk.get("page"),
                "chunk_id": chunk["chunk_id"],
                "score": score
            }
        )

    retrieve_time = time.perf_counter() - retrieve_start

    print("\n---------- RAG Retrieve Metrics ----------")

    print(
        f"Query Embedding:   {embedding_time:.3f}s"
    )

    print(
        f"FAISS Search:      {faiss_time:.3f}s"
    )

    print(
        f"Retrieve Total:    {retrieve_time:.3f}s"
    )

    print(
        f"Candidates:        {len(candidates)}"
    )

    print("------------------------------------------")


    return candidates

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = RERANK_TOP_K,
    min_rerank_score: float = RERANK_MIN_SCORE
)->list[dict]:

    rerank_start = time.perf_counter()

    if not candidates:
        return []

    # =========================
    # 1. 构造 query-document pairs
    # =========================

    pairs = []

    for candidate in candidates:
        pairs.append(
            [query,candidate["text"]]
        )

    # =========================
    # 2. Reranker 推理
    # =========================
    predict_start = time.perf_counter()

    rerank_scores = reranker_model.predict(pairs)

    predict_time = time.perf_counter() - predict_start

    # =========================
    # 3. 拼接结果
    # =========================

    reranked_results = []

    for candidate, score in zip(
            candidates,
            rerank_scores
    ):
        reranked_results.append(
            {
                "text": candidate["text"],
                "source": candidate["source"],
                "page": candidate.get("page"),
                "chunk_id": candidate["chunk_id"],
                "retrieval_score": candidate["score"],
                "rerank_score": float(score)
            }
        )

    # =========================
    # 4. 按 rerank score 排序
    # =========================
    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    # =========================
    # 5. 阈值过滤 + Top-K
    # =========================
    filtered_results = []

    for item in reranked_results:
        if item["rerank_score"] < min_rerank_score:
            break

        filtered_results.append(item)

        if len(filtered_results) >= top_k:
            break

    # =========================
    # 6. 耗时统计
    # =========================
    rerank_time = (
        time.perf_counter()
        - rerank_start
    )

    print("\n---------- RAG Rerank Metrics ----------")

    print(
        f"Reranker Predict: {predict_time:.3f}s"
    )

    print(
        f"Rerank Total:     {rerank_time:.3f}s"
    )

    print(
        f"Input Candidates: {len(candidates)}"
    )

    print(
        f"Final Results:    {len(filtered_results)}"
    )

    print("----------------------------------------")

    return filtered_results

def search_knowledge_base(
        query: str,
        top_k: int = 3
) -> list[dict]:

    rag_start = time.perf_counter()

    candidates = retrieve_candidates(
        query=query,
        top_n=RETRIEVAL_TOP_N,
        min_score=RETRIEVAL_MIN_SCORE
    )

    results = rerank(
        query=query,
        candidates=candidates,
        top_k=RERANK_TOP_K,
        min_rerank_score=RERANK_MIN_SCORE
    )

    rag_time = (
        time.perf_counter()
        - rag_start
    )

    print("\n========== RAG Metrics ==========")

    print(
        f"RAG Total:       {rag_time:.3f}s"
    )

    print(
        f"Candidates:      {len(candidates)}"
    )

    print(
        f"Final Results:   {len(results)}"
    )

    print("=================================\n")

    return results