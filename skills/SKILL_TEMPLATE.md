# Skill 编写范式

> 基于 phuryn/pm-skills 全量审计（23/68 + market-deep-research v1.1.0 + product-standards），提取的 Skill 编写标准。
> 所有 16 个 Skills 必须按此范式编写。

---

## 范式总览

```
---
name: skill-name
description: 一句话描述 + 触发条件 + 适用场景
---

# Skill Title

## 1. Purpose（目的）
本 Skill 解决什么问题？在 Agent 工作流中的位置？

## 2. Context（上下文/适用场景）
- 什么时候触发此 Skill？
- 需要什么前置条件（Gate 通过、上游文档就绪）？
- 输出被谁消费（下游 Skill 或人工 PM）？

## 3. Operating Principles（操作原则）
硬性规则，每条包含：
- 原则声明
- 反面行为描述（"不要……"）
- 违反后果

## 4. Instructions（分步骤指引）
Think Step by Step。每步包含：
- 输入：读什么文件/台账
- 操作：做什么
- 检查点：此步骤的完成条件

## 5. Output Structure（输出结构）
- 输出文件清单（Markdown 报告 + JSON/CSV 写入）
- 每个输出文件的完整模板（不是引用，是 copy-paste 可用的）
- 摘要章节格式规范

## 6. Quality Bar（最低质量标准）
可检查的完成条件列表，例如：
- [ ] 每条核心数据有 direct quote
- [ ] 所有 C 级源声明已标记 confidence
- [ ] 缺失维度已显式声明
- [ ] 输入来源表完整

Reviewer 将按此 checklist 逐项检查。

## 7. Tool Integration（工具链）
- 本 Skill 使用的工具及其边界
- 主工具不可用时的降级链
- 工具输出的质量门禁阈值

## 8. Best Practices（最佳实践）
- 示例：好的输出 vs 差的输出
- 常见陷阱

## 9. Further Reading（扩展阅读）
- 关联模板（templates/）
- 关联台账（registers/）
- 方法论参考（docs/architecture.md 第十三章）
- 参考 Skills（market-deep-research, product-standards）
```

---

## 编写检查清单

每个 SKILL.md 提交前必须通过：

- [ ] 9 个章节全部存在（Purpose / Context / Principles / Instructions / Output / Quality / Tools / Practices / Reading）
- [ ] Operating Principles ≥3 条，每条有反面行为描述
- [ ] Instructions 每步有明确的输入/操作/检查点
- [ ] Output Structure 包含完整的输出模板（不是引用链接）
- [ ] Quality Bar ≥3 条可量化检查项
- [ ] 输出不包含占位符（TBD / TODO / "根据实际情况调整"）
- [ ] 台账写入时机明确（立即/增量/人工确认后）
- [ ] 与其他 Skill 的输入输出契约对齐

---

## 反例（禁止模式）

### ✗ 禁止: 只有高层指导，没有可执行步骤

```markdown
## Instructions
1. 分析市场情况
2. 写出报告
```

### ✗ 禁止: 输出模板用引用代替

```markdown
## Output
参考 templates/01_xxx.md
```

### ✗ 禁止: Quality Bar 模糊

```markdown
## Quality Bar
- 报告质量要高
```

---

## 正例（目标模式）

### ✓ 目标: 每步有输入/操作/检查点

```markdown
## Instructions

### Step 1: 加载项目上下文
- 输入：读取 `project_profile.json` 和 Gate 1 审批记录
- 操作：提取目标市场、产品品类、技术关键词
- 检查点：9 个研究维度中至少确定 6 个可检索

### Step 2: 证据收集与分级
- 输入：Step 1 的关键词列表
- 操作：对每个维度执行搜索 → 提取 falsifiable claim → 标记 source_grade
- 检查点：每条 evidence 记录包含 evidence_id, direct_quote, source_grade, importance

### Step 3: 生成研究报告
- 输入：Step 2 的 evidence 集合
- 操作：按模板章节组织内容 → 写摘要 → 填输入来源表
- 检查点：摘要 ≤500字，输入来源表无"缺失"状态未说明的条目
```

### ✓ 目标: 输出模板完整可复制

```markdown
## Output Structure

### 输出文件
1. `output/<project>/market_study_report.md` — 完整报告
2. `registers/evidence.csv` — 新增 evidence 记录
3. `registers/assumptions.csv` — 新增 assumption 记录

### 报告结构
[完整的 markdown 模板，包括所有章节标题和表格]
```

---

## 新增维度说明

相比原 pm-skills 审计提取的范式（Purpose → Context → Instructions → Output → Best Practices → Further Reading），本模板新增了三个维度：

| 新增维度 | 来源 | 说明 |
|---------|------|------|
| **Quality Bar** | market-deep-research v1.1.0 | 量化标准 + 可检查的完成条件。不是模糊的"写一份好报告"，而是 Reviewer 可以逐项打勾的 checklist |
| **Operating Principles** | market-deep-research v1.1.0 | 13 条操作原则的提炼。每条原则含：原则声明、反面行为描述、违反后果 |
| **Tool Integration** | market-deep-research + product-standards | 工具边界定义 + 降级链（主工具不可用时的备选方案）+ 质量门禁阈值 |

此外，product-standards 的审计还贡献了两个架构模式：

| 架构模式 | 来源 | 说明 |
|---------|------|------|
| **Pipeline Architecture** | product-standards | 阶段化管道设计。每个 Phase 有明确的输入/输出 JSON 契约。Gate 在 Phase 之间，覆盖率 < 80% 不通过 |
| **Multi-Agent Parallel Pattern** | product-standards + market-deep-research | Analyst → 3×Retriever 并行 → Validator。每个 Agent 读独立的 System Prompt |

---

## 跨 Skill 一致性要求

所有 Skills 必须遵循以下全局约定：

### ID 格式
- evidence: `EV-{project}-{seq}`
- assumption: `A-{project}-{seq}`
- risk: `RISK-{project}-{seq}`
- decision: `DEC-{project}-{seq}`
- requirement: `REQ-{project}-{seq}`
- traceability: `T-{project}-{seq}`

### 台账写入时机
- **流式写入**（立即）：evidence, assumptions, risks — 发现即写入
- **同步写入**（文档产出时）：requirements — 与 PRD 同步
- **增量追加**（建立关联时）：traceability — 建立 evidence→requirement 关联时
- **人工确认后写入**（Gate 审批后）：decisions — Gate 批准后才落盘
- **阶段结束时写入**：method_learnings — 每阶段 + 项目复盘

### 摘要格式规范
所有研究报告的摘要章节必须包含：
1. 对路由有影响的发现
2. 对产品定义有约束的发现
3. 需要 PM 决策的开放问题
4. 什么新证据会改变结论

每项 ≤ 2 句话。总字数 ≤ 500 字。
