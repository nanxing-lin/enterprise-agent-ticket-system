<template>
  <div class="layout">
    <!-- 左侧：聊天主区域 -->
    <main class="chat-section">
      <header class="header">
        <div class="logo">🧠 Agent Flow</div>
        <div class="badge">企业数据分析版</div>
      </header>

      <div class="message-list" ref="messageListRef">
        <div class="message ai-message" v-if="messages.length === 0">
          <div class="avatar ai">AI</div>
          <div class="bubble">
            你好！我是企业智能工单 Agent。你可以让我帮你查数据，例如：<br/>
            <span class="highlight">"帮我查一下2023年10月华东区的退货主要原因，以及总共退了多少钱？"</span>
          </div>
        </div>

        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role === 'user' ? 'user-message' : 'ai-message']">
          <div v-if="msg.role === 'user'" class="avatar user">我</div>
          <div v-else class="avatar ai">AI</div>
          
          <div class="bubble" :class="{'error-bubble': msg.type === 'error'}">
            <div v-if="msg.type === 'tool_call'" class="tool-trace">
              <span class="tool-icon">⚡</span> Agent 执行了工具查询
            </div>
            
            <!-- 【新增优化】：如果正在打字输出中，且遇到了 Markdown 表格符号，暂时显示加载动画，防止出现乱码 -->
            <div v-else-if="index === messages.length - 1 && isLoading && msg.content.includes('|')" class="loading-text">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span> Agent 正在生成数据报表...
            </div>
            
            <!-- 正常渲染 Markdown -->
            <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>
        
        <div v-if="isLoading && !currentStreamText" class="message ai-message">
           <div class="avatar ai">AI</div>
           <div class="bubble typing-indicator">正在规划任务并思考...</div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-wrapper">
          <el-input
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入业务诉求，按 Enter 发送..."
            @keyup.enter.prevent="sendMessage"
            :disabled="isLoading"
            class="custom-input"
          />
          <el-button type="primary" class="send-btn" @click="sendMessage" :loading="isLoading">
            发送 <span class="shortcut">↵</span>
          </el-button>
        </div>
      </div>
    </main>

    <!-- 右侧：Agent 状态监控看板 -->
    <aside class="monitor-section">
      <div class="monitor-header">
        <h3>Agent 内部状态监控</h3>
        <div class="status-dot" :class="{ active: isLoading }"></div>
      </div>
      
      <div class="monitor-content">
        <div class="monitor-card" v-for="(tool, idx) in toolHistory" :key="idx">
          <div class="card-header">
            <span class="step-badge">Step {{ idx + 1 }}</span>
            <span class="tool-name">{{ tool.tool }}</span>
          </div>
          <div class="code-block">
            <pre>{{ tool.args }}</pre>
          </div>
        </div>
        <div class="empty-state" v-if="toolHistory.length === 0">
          等待 Agent 调用工具...
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'

const inputText = ref('')
const messages = ref([])
const isLoading = ref(false)
const messageListRef = ref(null)
const currentStreamText = ref('')
const toolHistory = ref([])

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputText.value.trim() || isLoading.value) return

  const userMsg = inputText.value
  messages.value.push({ role: 'user', content: userMsg })
  inputText.value = ''
  isLoading.value = true
  currentStreamText.value = ''
  toolHistory.value = []
  scrollToBottom()

  let currentAIMessage = null

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMsg })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() 

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace('data: ', '').trim()
          if (!dataStr) continue

          const data = JSON.parse(dataStr)

          if (data.type === 'content') {
            if (!currentAIMessage) {
              currentAIMessage = { role: 'ai', type: 'content', content: '' }
              messages.value.push(currentAIMessage)
            }
            currentAIMessage.content += data.content
            currentStreamText.value = currentAIMessage.content
            scrollToBottom()
          } 
          else if (data.type === 'tool_call') {
            currentAIMessage = null
            toolHistory.value.push({
              tool: data.tool,
              args: data.args.sql_query || JSON.stringify(data.args, null, 2)
            })
            messages.value.push({ role: 'ai', type: 'tool_call', content: '' })
            scrollToBottom()
          }
        }
      }
    }
  } catch (error) {
    console.error(error)
    messages.value.push({ role: 'ai', type: 'error', content: '⚠️ 后端连接失败，请检查服务是否启动。' })
  } finally {
    isLoading.value = false
    currentStreamText.value = ''
    scrollToBottom()
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', -apple-system, sans-serif;
  background-color: #0f172a;
  color: #e2e8f0;
  height: 100vh;
  overflow: hidden;
}

.layout { display: flex; height: 100vh; width: 100vw; }
.chat-section { flex: 1; display: flex; flex-direction: column; background: #0f172a; border-right: 1px solid #1e293b; position: relative; }
.header { padding: 20px 30px; display: flex; align-items: center; gap: 15px; border-bottom: 1px solid #1e293b; background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); z-index: 10; }
.logo { font-size: 20px; font-weight: 600; color: #fff; letter-spacing: 0.5px; }
.badge { background: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; border: 1px solid rgba(59, 130, 246, 0.3); }
.message-list { flex: 1; padding: 30px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; scroll-behavior: smooth; }
.message { display: flex; gap: 16px; max-width: 85%; }
.user-message { flex-direction: row-reverse; align-self: flex-end; }
.avatar { width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600; flex-shrink: 0; }
.avatar.ai { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; }
.avatar.user { background: #334155; color: #e2e8f0; }
.bubble { padding: 16px 20px; border-radius: 16px; line-height: 1.6; font-size: 15px; max-width: 100%; overflow-x: auto; }
.ai-message .bubble { background: #1e293b; border: 1px solid #334155; border-top-left-radius: 4px; color: #e2e8f0; }
.user-message .bubble { background: #3b82f6; color: white; border-top-right-radius: 4px; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3); }
.error-bubble { border-color: #ef4444; background: rgba(239, 68, 68, 0.1); color: #fca5a5; }

/* 优化后的加载动画样式 */
.loading-text {
  display: flex;
  align-items: center;
  color: #10b981;
  font-size: 14px;
  font-weight: 500;
}
.dot {
  width: 6px; height: 6px; background: #10b981; border-radius: 50%; margin-right: 4px;
  animation: bounce 1.4s infinite ease-in-out both;
}
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.highlight { color: #60a5fa; font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.tool-trace { display: flex; align-items: center; gap: 8px; color: #10b981; font-size: 13px; font-weight: 500; background: rgba(16, 185, 129, 0.1); padding: 8px 12px; border-radius: 8px; }
.input-area { padding: 20px 30px; background: #0f172a; border-top: 1px solid #1e293b; }
.input-wrapper { display: flex; gap: 12px; align-items: flex-end; background: #1e293b; padding: 12px; border-radius: 16px; border: 1px solid #334155; transition: border-color 0.2s; }
.input-wrapper:focus-within { border-color: #3b82f6; }
.custom-input :deep(.el-textarea__inner) { background: transparent; border: none; box-shadow: none; color: #e2e8f0; font-family: 'Inter', sans-serif; padding: 0; resize: none; font-size: 15px; }
.custom-input :deep(.el-textarea__inner::placeholder) { color: #64748b; }
.send-btn { background: #3b82f6; border: none; border-radius: 10px; height: 40px; padding: 0 20px; font-weight: 600; }
.send-btn:hover { background: #2563eb; }
.shortcut { opacity: 0.6; font-size: 12px; margin-left: 4px; }
.monitor-section { width: 400px; background: #0b1120; display: flex; flex-direction: column; }
.monitor-header { padding: 20px; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; }
.monitor-header h3 { font-size: 15px; font-weight: 500; color: #94a3b8; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: #475569; transition: background 0.3s; }
.status-dot.active { background: #10b981; box-shadow: 0 0 10px #10b981; }
.monitor-content { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.monitor-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; overflow: hidden; animation: slideIn 0.3s ease-out; }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.card-header { padding: 12px 16px; background: rgba(255,255,255,0.03); border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
.step-badge { background: #3b82f6; color: white; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }
.tool-name { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #94a3b8; }
.code-block { padding: 16px; background: #0f172a; }
.code-block pre { margin: 0; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #10b981; white-space: pre-wrap; word-break: break-all; }
.empty-state { text-align: center; color: #475569; font-size: 13px; margin-top: 40px; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { color: #f8fafc; margin-top: 16px; margin-bottom: 8px; font-weight: 600; }
.markdown-body :deep(p) { margin-bottom: 12px; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 20px; margin-bottom: 12px; }
.markdown-body :deep(li) { margin-bottom: 4px; }
.markdown-body :deep(table) { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; border-radius: 8px; overflow: hidden; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid #334155; padding: 10px 12px; text-align: left; }
.markdown-body :deep(th) { background: #1e293b; color: #e2e8f0; font-weight: 600; }
.markdown-body :deep(tr:nth-child(even)) { background: rgba(255,255,255,0.02); }
</style>