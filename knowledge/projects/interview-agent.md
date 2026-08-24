# 技术面试问答助手

## 项目背景

这是一个把候选人 Markdown 资料转成可追问问答的个人项目。使用者可以询问项目、技能和 GitHub 仓库，系统要求回答有资料依据，缺失数据时明确拒绝编造。

## 我的职责

我独立完成知识库结构、RAG 检索、LangGraph 工具调用、SSE 流式接口、Vue 聊天页面、Redis 限流和 Docker Compose 部署。界面设计以可用为主，没有进行专业视觉设计。

## 技术栈

Python 3.12、FastAPI、LangGraph、LangChain、Redis Vector Search、OpenAI-compatible API、Vue 3、TypeScript、Vite、Docker Compose、Nginx。

## 系统架构

浏览器通过 FastAPI SSE 接口发起问题。Agent 根据问题调用项目、技能、简历或 GitHub 工具；前三类资料来自 Redis 向量索引，GitHub 数据按需调用 REST API。LangGraph Checkpointer 保存会话上下文，使“这个项目为什么用 Redis”一类追问能够关联上一轮。

## 技术选型

选择 LangGraph 是因为流程需要显式的工具调用循环和会话状态，不需要复杂的多 Agent。选择 Markdown 作为事实源，是为了让资料可审阅、可版本管理，并能在删除索引后完整重建。选择 SSE 而不是 WebSocket，是因为当前交互只有客户端请求、服务端单向流式返回，SSE 的实现和代理配置更简单。

## Redis

Redis 承担四类相互隔离的用途：向量索引、对话 checkpoint、滑动窗口限流和 GitHub 响应缓存。重新索引只删除指定向量索引，不清空整个数据库。限流使用 Lua 脚本原子执行清理、计数和写入，避免并发请求突破阈值。

## 遇到的问题

早期版本直接把完整 Markdown 拼进系统提示，资料增加后上下文迅速膨胀，而且模型会混淆不同项目中的 Redis 用法。另一个问题是 Nginx 默认缓冲导致浏览器看起来像一次性返回，而不是逐 token 展示。

## 解决方案

我把资料按 Markdown 标题切块，为 chunk 添加 category、project、section 和 source 元数据，检索时先按类别过滤；项目明确时再按 slug 过滤。SSE 部署层关闭 `proxy_buffering`，并设计 `start/status/token/sources/done/error` 事件，前端用增量解析器处理跨 chunk 数据。

## 测试

后端用 fake embedding、fake vector store 和 mock HTTP 覆盖 loader、retriever、工具、GitHub 缓存、限流和 SSE；前端测试 SSE 分片与多事件粘包。测试不会调用收费模型或真实 GitHub 网络。

## 项目亮点

系统提示明确区分通用知识和候选人事实，资料未记录的团队规模、QPS 或成果必须回答未知；工具结果和 README 都按不可信输入处理，避免其中的文本变成高优先级指令。

## 性能数据

这是功能验证型个人项目，没有稳定线上流量，也没有记录并发用户数、准确率提升比例或商业成果。不能据此声称支持高并发生产负载。

## 可以改进的地方

目前检索只有向量相似度和元数据过滤。后续可以增加关键词混合检索、reranker 和离线问答评测集，但这些尚未实现。
