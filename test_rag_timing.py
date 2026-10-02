import time

from app.rag import search_knowledge_base


query = "VIP会员售后权益"


for i in range(5):

    print(
        f"\n\n========== 第 {i + 1} 次测试 =========="
    )

    start = time.perf_counter()

    results = search_knowledge_base(
        query=query,
        top_k=3
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        f"外层总耗时: {elapsed:.3f}s"
    )

    print(
        f"结果数量: {len(results)}"
    )