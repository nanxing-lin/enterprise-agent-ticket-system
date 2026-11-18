from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

# 导入刚才写好的 Agent 工作流
from app.agent.ticket_agent import ticket_agent_app

# 1. 初始化 FastAPI 应用
app = FastAPI(
    title="企业智能工单处理 Agent",
    description="基于 LangGraph + FastAPI 构建的企业级 ReAct Agent 后台",
    version="1.0.0"
)

# 2. 配置跨域（CORS）
# 这一步非常重要，等会儿你的 Vue 前端跑在别的端口（比如 5173），
# 如果不配置这个，浏览器会拦截前端发送给后端的请求。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，方便开发，上线后可改成具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. 定义请求体数据格式 (使用 Pydantic)
class ChatRequest(BaseModel):
    message: str


# 4. 基础测试路由
@app.get("/")
def read_root():
    return {"status": "success", "message": "Agent 服务已启动！请访问 /docs 查看接口文档。"}


# 5. 核心 Agent 聊天接口 (流式输出)
@app.post("/api/chat")
async def chat_with_agent(request: ChatRequest):
    """
    接收前端传来的用户提问，调用 Agent 进行多步推理，
    并以 SSE (Server-Sent Events) 的形式实时流式返回结果。
    """

    async def event_generator():
        # 构造 LangGraph 需要的初始状态
        initial_state = {"messages": [("user", request.message)]}

        try:
            # 使用 astream 进行异步流式遍历，实时捕获节点执行过程
            async for event in ticket_agent_app.astream(initial_state):
                for node_name, node_output in event.items():

                    # 确保节点有消息输出
                    if "messages" in node_output:
                        msg = node_output["messages"][-1]

                        # 情况 A：如果是大模型返回的文本内容（比如思考过程、最终报告）
                        if msg.content:
                            data = {
                                "node": node_name,
                                "type": "content",
                                "content": msg.content
                            }
                            # yield 把数据实时推给前端，格式必须符合 SSE 规范：data: xxx\n\n
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                        # 情况 B：如果是大模型决定调用工具（把 AI 生成的 SQL 展示给前端，显得很高级）
                        elif hasattr(msg, "tool_calls") and msg.tool_calls:
                            tool_call = msg.tool_calls[0]
                            data = {
                                "node": node_name,
                                "type": "tool_call",
                                "tool": tool_call['name'],
                                "args": tool_call['args']
                            }
                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        except Exception as e:
            # 捕获异常，防止后端崩溃
            error_data = {
                "node": "error",
                "type": "error",
                "content": f"Agent 执行异常: {str(e)}"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    # 返回流式响应，媒体类型必须是 text/event-stream
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ================= 启动入口 =================
if __name__ == "__main__":
    import uvicorn

    # 直接运行这个文件时，自动启动 uvicorn 服务器
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)