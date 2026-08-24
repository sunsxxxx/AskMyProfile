# Python 与 AI 应用开发

## 掌握程度

能够使用 Python、FastAPI、LangChain 和 LangGraph 开发带工具调用与 RAG 的应用，理解 embedding、chunk、metadata filter、会话状态和流式输出。没有训练基础模型或微调大模型的经历。

## 实际使用

在“技术面试问答助手”中实现 Markdown 标题切块、Redis 向量检索、四类资料工具、LangGraph 工具循环和 FastAPI SSE 输出。

## 解决的问题

通过 category 与 project 元数据过滤减少不同资料类型和不同项目之间的串扰；通过事实约束提示词，要求候选人数据必须有工具结果支持。工具结果按不可信数据处理。

## 评测边界

目前只有单元测试和人工问题验证，没有建立标注问答集，也没有召回率、忠实度或幻觉率等量化评测结果。

## 复盘

下一步希望补充混合检索、reranker 和离线评测。上述能力目前尚未在项目中实现，不能作为已有成果描述。
