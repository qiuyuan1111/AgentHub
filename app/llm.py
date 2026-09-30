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

def summarize_memory(
    old_summary: str,
    messages: list[dict]
) -> str:
    if not messages:
        return old_summary

    conversation_text = "\n".join(
        f'{message["role"]}: {message["content"]}'
        for message in messages
    )

    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {
                "role": "system",
                "content":  (
                    "你负责维护一份简洁、准确的会话记忆摘要。"
                    "请根据旧摘要和新增对话，生成更新后的摘要。"
            
                    "只保留未来对话中可能有用的信息，"
                    "例如用户明确提供的订单号、商品编号、"
                    "已经讨论的重要事实、用户当前目标、"
                    "尚未解决的问题以及必要的上下文。"
            
                    "对于订单状态、商品库存等可能随时间变化的业务信息，"
                    "应优先保留订单号、商品编号等用于后续指代解析的信息。"
                    "如果需要保留历史状态，应明确这是此前查询时的结果，"
                    "不得把历史状态描述成当前仍然有效的事实。"
            
                    "不要编造对话中不存在的信息。"
                    "不要把临时寒暄或无意义内容写入摘要。"
            
                    "如果新对话修改或否定了旧信息，"
                    "应以较新的信息为准。"
            
                    "摘要应简洁，直接输出摘要正文，"
                    "不要输出解释、标题或其他额外内容。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"旧摘要:\n"
                    f"{old_summary or '无'}\n\n"
                    
                    f"新增对话:\n"
                    f"{conversation_text}"
                )
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()

def chat_with_tools(
    message: str,
    history: list[dict],
    summary: str = ""
) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "你是 AgentHub 企业智能助手。"
    
                "对于订单状态、商品库存等业务问题，"
                "可以调用对应的业务工具获取信息。"
    
                "对于公司政策、退款、售后、会员规则、员工服务等知识类问题，"
                "必须优先调用知识库检索工具查询相关内容。"
    
                "涉及公司政策或业务规则的事实性结论，"
                "只能依据业务工具或知识库检索结果中的内容回答。"
                "不得自行补充知识库中不存在的流程、条件、要求、例外情况、"
                "时间范围、处理方式或其他事实。"
    
                "如果知识库返回的内容不足以回答用户的问题，"
                "应明确说明当前知识库中没有检索到足够的信息，"
                "不要根据常识、经验或猜测补充答案。"
    
                "回答知识库相关问题时，"
                "应优先直接回答用户的问题，"
                "再在答案末尾注明实际使用到的知识来源。"
    
                "知识库检索结果中的 source 字段表示知识来源文件，"
                "page 字段表示该知识片段所在的 PDF 页码。"
    
                "如果检索结果的 page 不为空，"
                "来源统一写成“来源：文件名，第N页”的格式。"
    
                "如果检索结果的 page 为空，"
                "来源统一写成“来源：文件名”的格式。"
    
                "来源和页码必须严格依据知识库工具返回的 source 和 page 字段，"
                "不得自行编造、修改、推测或补全文件名和页码。"
    
                "如果多个实际使用的知识片段来自同一个 source 和同一页，"
                "只需要列出一次。"
    
                "如果多个实际使用的知识片段来自同一个 source 但不同页，"
                "应分别列出实际使用到的页码。"
    
                "如果答案使用了多个不同 source 的知识片段，"
                "应分别列出所有实际使用到的来源。"
    
                "不要为了展示来源而列出与最终答案无关的检索结果。"
    
                "回答时应简洁、准确，"
                "避免加入知识库或业务工具没有提供的额外建议。"

                "不要声称已经永久保存、长期记住或持久记录用户提供的信息。"
                "只能基于当前会话上下文理解和引用此前内容。"
            )
        }
    ]

    if summary:
        messages.append(
            {
                "role": "system",
                "content": (
                    "下面是较早会话内容的压缩摘要，"
                    "仅用于帮助理解用户当前问题中的上下文和指代：\n"
                    f"{summary}\n"

                    "如果摘要与最近对话存在冲突，"
                    "应以最近对话为准。"

                    "订单状态、商品库存等可能变化的业务信息，"
                    "不能仅依据历史摘要作为当前事实，"
                    "如用户询问当前状态，应重新调用对应业务工具确认。"
                )
            }
        )

    # 加入历史对话
    if history:
        messages.extend(history)

    # 加入当前这一轮用户消息
    messages.append(
        {
            "role": "user",
            "content": message
        }
    )

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