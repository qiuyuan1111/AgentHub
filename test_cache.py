from app.llm import make_tool_cache_key

key1 = make_tool_cache_key(
    "search_knowledge_base",
    {
        "query": "VIP会员售后权益",
        "top_k": 3
    }
)

key2 = make_tool_cache_key(
    "search_knowledge_base",
    {
        "query": "   VIP会员售后权益   ",
        "top_k": 3
    }
)

key3 = make_tool_cache_key(
    "get_order_status",
    {
        "order_id": "1001"
    }
)

print(key1)
print(key2)
print(key1 == key2)
print(key3)