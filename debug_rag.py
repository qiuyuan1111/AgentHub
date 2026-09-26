from app.rag import retrieve_candidates, rerank


query = "商品坏了怎么办？"


candidates = retrieve_candidates(
    query=query,
    top_k=10,
    min_score=0.0
)


print("===== Retriever =====")

for index, item in enumerate(candidates, start=1):
    print(f"\n结果 {index}")
    print("文本:", item["text"])
    print("来源:", item["source"])
    print("Chunk ID:", item["chunk_id"])
    print("Retrieval分数:", item["score"])


results = rerank(
    query=query,
    candidates=candidates,
    top_k=10,
    min_rerank_score=0.0
)


print("\n===== Reranker =====")

for index, item in enumerate(results, start=1):
    print(f"\n结果 {index}")
    print("文本:", item["text"])
    print("来源:", item["source"])
    print("Chunk ID:", item["chunk_id"])
    print("Retrieval分数:", item["retrieval_score"])
    print("Rerank分数:", item["rerank_score"])