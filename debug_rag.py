from app.rag import retrieve_candidates, rerank


query = "退款什么时候到账？"


candidates = retrieve_candidates(
    query=query,
    top_n=20,
    min_score=0.0
)


print("===== Retriever 原始结果 =====")

for index, item in enumerate(candidates, start=1):
    print(f"\n结果 {index}")
    print("文本:", item["text"])
    print("来源:", item["source"])
    print("页码:", item.get("page"))
    print("Chunk ID:", item["chunk_id"])
    print("Retrieval分数:", item["score"])


results = rerank(
    query=query,
    candidates=candidates,
    top_k=20,
    min_rerank_score=0.0
)


print("\n===== Reranker 原始结果 =====")

for index, item in enumerate(results, start=1):
    print(f"\n结果 {index}")
    print("文本:", item["text"])
    print("来源:", item["source"])
    print("页码:", item.get("page"))
    print("Chunk ID:", item["chunk_id"])
    print("Retrieval分数:", item["retrieval_score"])
    print("Rerank分数:", item["rerank_score"])