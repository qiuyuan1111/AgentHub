from app.llm import execute_tool_with_cache


tool_cache = {}

tool_state = {
    "rag_search_count": 0
}


result1, hit1 = execute_tool_with_cache(
    function_name="search_knowledge_base",
    arguments={
        "query": "VIP会员售后权益"
    },
    tool_cache=tool_cache,
    tool_state=tool_state
)

print("第一次:")
print("cache hit:", hit1)
print("count:", tool_state["rag_search_count"])
print(result1)


result2, hit2 = execute_tool_with_cache(
    function_name="search_knowledge_base",
    arguments={
        "query": "退款到账时间"
    },
    tool_cache=tool_cache,
    tool_state=tool_state
)

print("\n第二次:")
print("cache hit:", hit2)
print("count:", tool_state["rag_search_count"])
print(result2)


result3, hit3 = execute_tool_with_cache(
    function_name="search_knowledge_base",
    arguments={
        "query": "商品质量问题售后"
    },
    tool_cache=tool_cache,
    tool_state=tool_state
)

print("\n第三次:")
print("cache hit:", hit3)
print("count:", tool_state["rag_search_count"])
print(result3)