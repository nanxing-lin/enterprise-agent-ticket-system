# 🤖 企业智能工单处理 Agent (Enterprise Agent Ticket System)

这是一个基于大模型**自主规划（ReAct）**的企业级数据分析网页。用户输入模糊的业务诉求，Agent 会自动拆解任务、编写 SQL 语句、查询企业数据库，并生成结构化的 Markdown 分析报告。

## 🔗 在线体验
👉 **[点击这里直接体验项目](http://121.41.178.89:8080)** *(请在电脑端打开体验流式输出效果)*

## ✨ 核心功能
- **Agent 自主规划**：基于 `LangGraph` 构建 ReAct 状态图，AI 能自主完成“思考-查询-修正-总结”闭环。
- **流式打字机交互**：前后端通过 `SSE (Server-Sent Events)` 实现流式输出，前端实时接收大模型生成内容。
- **Agent 状态监控看板**：前端右侧实时高亮展示 AI 自动生成的 SQL 语句，让 AI 的思考过程不再是“黑盒”。
- **企业级安全防护**：底层 SQLite 数据库强制设置**只读模式 (Read-Only)**，限制查询返回行数，有效防止 AI 幻觉导致的删库或 Token 爆炸。

## 🛠️ 技术栈
- **前端**: Vue3 / Element Plus / Vite / marked.js
- **后端**: Python / FastAPI / LangGraph / LangChain
- **数据库**: SQLite
- **部署**: Docker / Docker Compose / Nginx / 阿里云 ECS

## 📸 界面预览
*(在这里插入一张你项目的截图！可以将截图拖拽到 GitHub 编辑框里自动生成图片链接)*
