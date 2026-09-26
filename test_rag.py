from app.rag import search_knowledge_base

queries = [
    "数字商品可以七天无理由退款吗？",
    "商品坏了怎么办？",
    "退款什么时候到账？",
    "VIP会员有什么售后权益？",
    "公司CEO是谁？"
]

for query in queries:

    print("\n" + "=" * 60)
    print("问题:", query)

    results = search_knowledge_base(query)

    if not results:
        print("没有检索到相关内容")
        continue

    for index, result in enumerate(results, start=1):
        print(f"\n结果 {index}")
        print("文本:", result["text"])
        print("来源:", result["source"])
        print("Chunk ID:", result["chunk_id"])
        print("Retrieval分数:", result["retrieval_score"])
        print("Rerank分数:", result["rerank_score"])