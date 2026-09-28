from app.rag import search_knowledge_base

TEST_CASES = [
    {
        "query": "数字商品可以七天无理由退款吗？",
        "expected_sources": [
            "refund_policy.txt",
            "test_policy.pdf"
        ]
    },
    {
        "query": "商品坏了怎么办？",
        "expected_sources": [
            "after_sales.md",
            "test_policy.pdf"
        ]
    },
    {
        "query": "VIP会员有什么售后权益？",
        "expected_sources": [
            "vip_policy.txt"
        ]
    },
    {
        "query": "公司CEO是谁？",
        "expected_sources": []
    },
    {
        "query": "员工服务申请多久完成审核？",
        "expected_sources": [
            "test_policy.pdf"
        ]
    },
    {
        "query": "退款什么时候到账？",
        "expected_sources": [
            "refund_policy.txt"
        ]
    }
]

def evaluate():

    total = len(TEST_CASES)

    passed = 0

    hit_at_1 = 0
    hit_at_3 = 0

    negative_total = 0
    negative_correct = 0

    for case in TEST_CASES:

        query = case["query"]
        expected_sources = case["expected_sources"]

        results = search_knowledge_base(
            query=query,
            top_k=3
        )

        retrieved_sources = [
            result["source"]
            for result in results
        ]

        print("=" * 60)
        print("问题:", query)

        # ---------------------------
        # 负样本
        # ---------------------------

        if not expected_sources:

            negative_total += 1

            if not results:
                print("[PASS] 正确拒绝")
                passed += 1
                negative_correct += 1
            else:
                print("[FAIL] 本应没有结果")

                print(
                    "实际来源:",
                    retrieved_sources
                )
            continue

        # ---------------------------
        # 正样本
        # ---------------------------

        hit1 = any(
            source in expected_sources
            for source in retrieved_sources[:1]
        )

        hit3 = any(
            source in expected_sources
            for source in retrieved_sources[:3]
        )

        if hit1:
            hit_at_1 += 1

        if hit3:
            hit_at_3 += 1
            print("[PASS]")
            passed += 1

        else:
            print("[FAIL]")

        print(
            "期望来源:",
            expected_sources
        )

        print(
            "实际来源:",
            retrieved_sources
        )

        print(
            "Hit@1:",
            hit1
        )

        print(
            "Hit@3:",
            hit3
        )

    # ---------------------------
    # 汇总
    # ---------------------------

    print("\n" + "=" * 60)

    print(
        f"整体通过：{passed}/{total}"
    )

    print(
        f"整体通过率：{passed / total:.2%}"
    )

    positive_total = total - negative_total

    if positive_total > 0:

        print(
            f"Hit@1："
            f"{hit_at_1}/{positive_total} "
            f"= {hit_at_1 / positive_total:.2%}"
        )

        print(
            f"Hit@3："
            f"{hit_at_3}/{positive_total} "
            f"= {hit_at_3 / positive_total:.2%}"
        )

    if negative_total > 0:

        print(
            f"负样本拒绝率："
            f"{negative_correct}/{negative_total} "
            f"= {negative_correct / negative_total:.2%}"
        )

if __name__ == "__main__":
    evaluate()