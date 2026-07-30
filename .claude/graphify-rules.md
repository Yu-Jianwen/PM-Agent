# 项目协作规则

## Graphify 使用边界

- 本项目禁止自动调用、查询、更新或重建 Graphify。
- 回答项目内容、文档关系、架构或文件问题时，默认直接读取源文件，并优先使用 `rg` 定位证据。
- 即使 `graphify-out/graph.json` 已存在，也不得把自然语言项目问题自动路由到 `graphify query`。
- 只有当用户在当前请求中明确要求使用 Graphify、更新知识图谱、查询图谱、查找图路径或解释图节点时，才可以使用 Graphify。
- 不得自动启动 `graphify --watch`、MCP 服务、提交 hook 或其他后台更新机制。
- `graphify-out/` 是可选的生成产物，不是项目事实来源、业务主数据或工作流运行依赖；其内容不得替代 Markdown 源文档、registers 台账和确定性校验结果。

