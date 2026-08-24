# 个人知识库使用说明

`knowledge/` 是本项目关于候选人经历的唯一事实源（Source of Truth）。Redis 只保存可重建索引；请勿直接在 Redis 中维护个人资料。

> 当前 `projects/` 与 `skills/` 中的内容是本地问答演示用模拟数据，不对应真实公司或个人经历。`README.md` 不会进入向量索引；替换为真实资料时请删除本说明和现有模拟文件。

## 建议目录

```text
knowledge/
├── profile/introduction.md
├── education/education.md
├── experience/internship.md
├── projects/<project-slug>.md
├── skills/<skill>.md
└── interview/interview-notes.md
```

当前仅提供 `examples/` 示例，Agent 会把它识别为示例而不当作真实经历。请复制模板到对应的真实分类目录，替换所有占位内容后删除示例文件，再运行重新索引。

## 项目资料模板

```markdown
# 项目名称

## 项目背景

## 我的职责

## 技术栈

## 系统架构

## 核心模块

## 技术选型

## Redis

## MySQL

## RabbitMQ

## 遇到的问题

## 解决方案

## 性能优化

## 项目亮点

## 可以改进的地方
```

写作原则：只写可核实事实；涉及 QPS、业务量、提升比例和团队人数时给出真实口径，无法公开的内容明确写“不可公开”，不要用估算值填充。一级标题会成为资料标题，二/三级标题会成为检索 section，项目文件名会成为 `project` 过滤字段。
