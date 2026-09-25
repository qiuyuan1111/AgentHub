from app.rag import search_knowledge_base

query = "数字商品可以七天无理由吗？"

results = search_knowledge_base(query)

for index, result in enumerate(
    results,
    start=1
):
    print(f"\n结果 {index}")
    print("文本:", result["text"])
    print(
        "Embedding分数:",
        result["retrieval_score"]
    )
    print(
        "Rerank分数:",
        result["rerank_score"]
    )