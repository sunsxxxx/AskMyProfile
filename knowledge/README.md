# 个人知识库使用说明

`knowledge/` 是本项目关于候选人经历的唯一事实源（Source of Truth）。Redis 只保存可重建索引；请勿直接在 Redis 中维护个人资料。

当前 profile、experience、projects 与 skills 条目均依据本地工程源码核验整理。`README.md` 不会进入向量索引；后续维护仍须确保每项经历、技术机制和边界都能追溯到代码或真实资料。

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

生产知识集不保留 `examples/` 示例。新增资料时请放入对应分类目录，使用清晰的一级标题和二/三级章节，并在静态加载检查通过后再决定是否重新索引。

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
