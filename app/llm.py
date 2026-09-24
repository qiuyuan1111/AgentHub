import os
import json



from app.tools import get_order_status
from app.tools import TOOL_FUNCTIONS

from dotenv import load_dotenv
from openai import OpenAI

# 读取 .env 文件
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("没有读取到 DEEPSEEK_API_KEY, 请检查 .env 文件")

# 创建大模型客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "根据订单编号查询订单当前状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单编号，例如1001"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_stock",
            "description": "根据商品编号查询商品当前库存",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "商品编号,例如 P001"
                    }
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "从公司知识库中检索与用户问题相关的公司政策、售后规则、退款规则等信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要在公司知识库中检索的问题"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回最相关的知识片段数量，默认3"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def chat(message:str):
    messages = [
        {
            "role": "system",
            "content": "你是 AgentHub 中的 AI 助手。"
        },
        {
            "role": "user",
            "content": message
        }
    ]
    # 向大模型发送请求
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=messages
    )



    # 输出模型回答
    return response.choices[0].message.content
def chat_with_tools(message:str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "你是 AgentHub 企业智能助手。"
                "对于订单、库存等业务问题，可以调用对应工具。"
                "对于公司政策、售后规则等问题，应优先查询知识库。"
                "如果知识库没有检索到相关内容，不要自行编造，"
                "应告诉用户当前知识库中没有找到相关信息。"
            )
        },
        {
            "role": "user",
            "content": message
        }
    ]

    max_step = 5

    for step in range(max_step):
        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=tools
        )



        assistant_message = response.choices[0].message

        print(f"\n===== Agent Step {step + 1} =====")
        print("LLM 返回：", assistant_message)

        # 如果模型不需要工具，直接返回回答
        if not assistant_message.tool_calls:
            return assistant_message.content
        # 记录模型发出的 Tool Call
        messages.append(assistant_message)

        # 执行这一轮的所有 Tool Call
        for tool_call in assistant_message.tool_calls:

            # 得到工具名称
            function_name = tool_call.function.name

            # 得到工具参数
            arguments = json.loads(tool_call.function.arguments)

            # 执行工具
            tool_function = TOOL_FUNCTIONS.get(function_name)
            if not tool_function:
                tool_result = "未知工具"
            else:
                tool_result = tool_function(**arguments)

            if isinstance(tool_result, str):
                tool_result_text = tool_result
            else:
                tool_result_text = json.dumps(
                    tool_result,
                    ensure_ascii=False
                )

            print("模型选择的工具: ", function_name)
            print("模型生成的参数: ", arguments)
            print("工具执行结果: ", tool_result)


            # 告诉模型 Tool 的真实执行结果
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_text
                }
            )



    return "任务执行步骤过多,请稍后重试。"