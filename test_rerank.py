from app.rag import rerank, retrieve_candidates

query = "数字商品可以七天无理由退款吗？"

candidates = retrieve_candidates(
    query=query,
    top_k=5,
    min_score=0.5
)

print("===== Embedding Retrieval =====")

for index, item in enumerate(candidates, start=1):
    print(f"\n结果 {index}")
    print("文本：", item["text"])
    print("Embedding分数：", item["score"])

results = rerank(
    query=query,
    candidates=candidates,
    top_k=3
)

print("\n===== Reranker =====")

for index, item in enumerate(results, start=1):
    print(f"\n结果 {index}")
    print("文本：", item["text"])
    print("原始Embedding分数：", item["retrieval_score"])
    print("Rerank分数：", item["rerank_score"])
