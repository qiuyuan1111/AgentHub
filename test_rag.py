from app.rag import search_knowledge_base

results = search_knowledge_base(
    "数字商品可以七天无理由吗？"
)

for index, result in enumerate(results, start=1):
    print(f"结果 {index}")
    print("文本：", result["text"])
    print("相似度：", result["score"])
    print()