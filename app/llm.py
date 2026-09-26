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
    
                "对于订单状态、商品库存等业务问题，可以调用对应的业务工具获取信息。"
    
                "对于公司政策、退款、售后、会员规则等知识类问题，"
                "必须优先调用知识库检索工具查询相关内容。"
    
                "涉及公司政策或业务规则的事实性结论，"
                "只能依据工具或知识库返回的内容回答，"
                "不得自行补充知识库中不存在的流程、条件、要求、例外情况或处理方式。"
    
                "如果知识库返回的内容不足以回答用户的问题，"
                "应明确说明当前知识库中未检索到相关信息，"
                "不要根据常识、经验或猜测补充答案。"
    
                "当知识库检索结果包含 source 字段时，"
                "回答知识库相关问题时，应在答案末尾注明所依据的知识来源。"
                "来源必须严格使用工具返回的 source 字段，"
                "不得自行编造、修改或猜测来源名称。"
    
                "如果多个有效知识片段来自同一个 source，只需列出一次该来源；"
                "如果来自多个 source，则分别列出所有实际使用到的来源。"
    
                "回答时应优先直接回答用户的问题，"
                "避免加入知识库或业务工具没有提供的额外建议。"
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