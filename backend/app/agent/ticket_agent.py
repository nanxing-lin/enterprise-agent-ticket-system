from typing import Annotated, TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 导入你写的工具，以及环境配置
from app.tools.database_tools import execute_sql_query
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


# 1. 定义状态：Agent 在图中流转时携带的数据（主要是对话历史）
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


# 2. 初始化大模型
llm = ChatOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    model=LLM_MODEL,
    temperature=0  # 设为0，让AI更严谨，避免胡乱发散
)

# 3. 绑定工具：告诉大模型“你有这个工具可以用”
tools = [execute_sql_query]
llm_with_tools = llm.bind_tools(tools)

# 4. 定义系统提示词 (System Prompt) - Agent 的灵魂
SYSTEM_PROMPT = """你是一个专业的企业数据分析 Agent。
你的任务是接收用户的业务诉求，通过查询数据库进行分析，并给出结构化的结论。

你目前可以使用以下工具：
- execute_sql_query: 用于在企业的 SQLite 数据库中执行 SQL 语句。

工作原则：
1. 遇到模糊的诉求（如“上个月华东区退货太多”），你必须先构思如何查数据，然后调用工具。
2. 数据库只有两张表：orders（订单表）和 returns（退货表），字段包含 region, product_name, total_amount, return_reason 等。
3. 你可能需要多次调用工具（比如先查总销售额，再查退款金额，最后做对比）。
4. 如果查询结果不满意，可以换个角度重写 SQL 再次查询。
5. 获取到足够数据后，停止调用工具，直接用清晰的 Markdown 格式输出分析报告。
"""


# 5. 定义 Agent 节点（大脑思考）
def agent_node(state: AgentState):
    # 每次思考时，把系统提示词加上
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# 6. 定义条件路由（决定下一步是继续用工具，还是直接结束）
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # 如果大模型决定调用工具，就去 "tools" 节点
    if getattr(last_message, "tool_calls", None):
        return "continue"
    # 否则，说明分析完了，结束
    return "end"


# ================= 7. 构建 LangGraph 工作流 =================
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))  # LangGraph 自带的工具执行节点

# 设置入口点
workflow.set_entry_point("agent")

# 添加条件边（从 agent 出发，根据 should_continue 决定去哪）
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",  # 去执行工具
        "end": END  # 结束
    }
)

# 添加普通边（工具执行完后，必须回到 agent 继续思考）
workflow.add_edge("tools", "agent")

# 编译成可运行的 App
ticket_agent_app = workflow.compile()

# ================= 8. 本地测试代码 =================
if __name__ == "__main__":
    print("=== 企业智能工单 Agent 启动 ===")
    user_input = "帮我查一下2023年10月华东区的退货主要原因，以及总共退了多少钱？"
    print(f"用户诉求: {user_input}\n")

    # 构建初始状态
    initial_state = {"messages": [("user", user_input)]}

    print("--- 开始推理 ---")
    # 运行 Agent (使用 stream 实时打印过程)
    for event in ticket_agent_app.stream(initial_state):
        for node_name, node_output in event.items():
            if "messages" in node_output:
                msg = node_output["messages"][-1]

                # 打印大模型的思考或最终回答
                if msg.content:
                    print(f"\n[{node_name} 节点] 输出内容:\n{msg.content}")

                # 打印工具调用信息
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    print(f"\n[{node_name} 节点] 决定调用工具: {msg.tool_calls[0]['name']}")
                    print(f"[{node_name} 节点] 生成的参数 (SQL): {msg.tool_calls[0]['args']}")

    print("\n--- 执行结束 ---")