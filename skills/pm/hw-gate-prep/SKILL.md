---
name: hw-gate-prep
description: PM Agent 门径准备技能。当某一阶段的所有成果物产出完毕且通过 Reviewer 审查后触发，生成 Gate 摘要文档 + gate-request.json，提交人类 PM 审批，人工确认后写入 decisions.csv。触发条件：阶段成果物 + Reviewer findings 就绪，需要进入下一 Gate。
---

# hw-gate-prep — 门径准备与审批

## 1. Purpose（目的）

本 Skill 负责智能硬件 PM Agent 流程中的人工门径（Gate）准备工作。在每个阶段的所有成果物产出且通过 Reviewer 审查后，PM Agent 汇总该阶段产出、运行前置校验、生成 Gate 摘要（含选项分析和风险评估），提交人类 PM 审批，并在**人工确认后**才将决策写入 decisions.csv。

在 Agent 工作流中的位置：每个阶段末尾的 Gate 节点，是阶段之间的质量闸门和路由控制点。

## 2. Context（上下文/适用场景）

### 触发条件
- 当前阶段的所有必需成果物已产出且通过 Reviewer 审查（hw-review verdict 不为 `pending`）
- hw-intake 已完成（已知路由等级 L1/L2/L3）
- 上一个 Gate 已批准（非首个 Gate 时）

### 前置条件
- 所有阶段成果物文件存在且版本明确
- Reviewer findings 已产出（verdict 不为 `pending`，无未解决的 blocker 级 finding）
- registers/ 目录下的 CSV 台账文件可读取

### 输出被谁消费
- **人工 PM**：阅读 Gate 摘要文档，做出 approve / reject / conditional-approve 决策
- **下一阶段的 PM Skill**：Gate 批准后，下一阶段 Skill 读取 decisions.csv 确认可继续
- **hw-handoff / hw-retro**：最终交付或复盘时，decisions.csv 提供完整决策链

### 路由与 Gate 对应关系

| 路由 | Gate 数量 | 适用 Gate |
|------|----------|-----------|
| L1 降本/衍生 | 3 个 | Gate 1, Gate 2, Gate 3 |
| L2 产品衍生 | 5 个 | Gate 1, Gate 2, Gate 3, Gate 4, Gate 5 |
| L3 新品类 | 7 个 | Gate 1, Gate 2, Gate 3, Gate 4, Gate 5, Gate 6, Gate 7 |

### Gate 位置与条件（对齐 AGENTS.md 第 6 节）

| Gate | 位置 | 必需成果物 | 审批人职责 |
|------|------|-----------|-----------|
| Gate 1 | hw-intake 完成后 | 启动卡 + 路由判定 + 任务包 | 批准项目路线（L1/L2/L3）和任务范围 |
| Gate 2 | 市场研究 + 用户研究完成后 | 市场研究报告 + 用户研究报告 + Reviewer 通过 | 确认研究充分，可进入竞品分析 |
| Gate 3 | 竞品分析完成后 | 竞品分析报告 + Reviewer 通过 | 确认竞品理解充分 |
| Gate 4 | 产品规划完成后 | 产品规划报告 + Reviewer 通过 | 确认"三定"方向正确 |
| Gate 5 | MRD/BRD 完成后 | MRD/BRD + Reviewer 通过 | 确认商业可行性 |
| Gate 6 | 产品定义完成后 | 产品定义文档 + Reviewer 通过 | 确认产品边界清晰 |
| Gate 7 | PRD + 验证计划完成后 | PRD + 验证计划 + Reviewer 通过 | 确认可进入开发 |

## 3. Operating Principles（操作原则）

### 原则 1：决策写入必须等人确认
decisions.csv 的写入时机是 **人工 PM 明确确认决策后**，绝不在此之前写入。

- **不要**：在生成 Gate 摘要时自动写入一条"建议批准"的 decision 记录。
- **不要**：在人工 PM 尚未回复时就假定审批结果并写入。
- **不要**：用任何自动化逻辑替代人工判断来决定 Gate 通过与否。
- **违反后果**：decisions.csv 中出现未经人工确认的 decision 记录，破坏决策链的可追溯性和合规性。后续阶段引用未经确认的 decision → 整个产品决策链路无效。

### 原则 2：前置校验不通过，不提交 Gate
4 项前置校验缺一不可。任何一项未通过时，不得向人工 PM 提交 Gate 审批请求。

- **不要**：跳过校验或仅打印警告后继续提交 Gate。
- **不要**：在校验失败时手动修改 gate-request.json 中的 `validation_status` 为 true。
- **不要**：将"校验失败但我知道原因"等同于"校验通过"。
- **违反后果**：台账不一致、追踪链断裂、未审查成果物进入下一阶段 → 返工成本成倍放大。人工 PM 基于错误数据进行决策 → 信任破产。

### 原则 3：选项分析必须提供真实替代方案
每个 Gate 摘要必须包含至少 2 个真实选项，且"不通过/回退/终止"必须是一个有效选项。

- **不要**：提供 3 个选项但 2 个是"继续"的变体、实质上只有一条路。
- **不要**：将 Agent 的建议写成唯一的合理选择。
- **不要**：隐藏或淡化不通过选项的风险和合理性。
- **不要**：用模糊语言掩盖选项之间的关键差异。
- **违反后果**：人工 PM 无法做出真正的知情决策 → Gate 审批沦为形式 → "橡皮图章"效应。当项目后期出现问题时，无人能回溯当初为什么选这条路。

### 原则 4：Gate 识别必须精确匹配 AGENTS.md
当前处于哪个 Gate 的判定必须严格对照 AGENTS.md 第 6 节的 Gate 位置与条件表，不能凭经验猜测。

- **不要**：基于"感觉这个阶段做完了"来判断当前 Gate。
- **不要**：混淆 L1/L2/L3 路由下的 Gate 数量和条件差异。
- **不要**：跳过中间 Gate 或将多个 Gate 合并处理。
- **违反后果**：Gate 序列错乱 → 流程完整性破坏 → 某些成果物未经审批进入下游 → 合规风险。

### 原则 5：Reviewer findings 必须完整覆盖所有成果物
Gate 提交前，当前 Gate 要求的每一项成果物必须有对应的 Reviewer verdict。任一成果物 verdict 为 `pending` 或存在未解决的 blocker finding，不得提交 Gate。

- **不要**：仅检查"有没有 findings 文件"而不检查每条 artifact 是否都有 verdict。
- **不要**：忽略 conditional approval 中的条件是否已满足。
- **不要**：将 blocker finding 降级处理或标注为"已知但不影响"后跳过。
- **违反后果**：未审查的成果物进入 Gate → 质量问题逃逸至下游 → Reviewer 机制失效。

## 4. Instructions（分步骤指引）

### Step 1：识别当前 Gate

- **输入**：
  - 读取 `output/<project>/` 目录，列出所有已产出成果物及其版本
  - 读取 `registers/decisions.csv`，列出已批准的 Gate 决策
  - 读取 hw-intake 产出中的路由判定（L1/L2/L3）

- **操作**：
  1. 根据路由等级确定 Gate 序列（L1 → Gate 1-3, L2 → Gate 1-5, L3 → Gate 1-7）
  2. 对照 AGENTS.md 第 6 节的 Gate 位置与条件表，逐 Gate 检查：
     - 该 Gate 要求的成果物是否全部存在且有明确版本号
     - 该 Gate 是否已有批准的 decision（在 decisions.csv 中 status=approved）
  3. 找到第一个**成果物已就绪**但**尚未有批准 decision**的 Gate，作为当前 Gate

- **检查点**：
  - [ ] 路由等级（L1/L2/L3）已从 hw-intake 确认
  - [ ] 当前 Gate ID（Gate1-Gate7）已在路由范围内
  - [ ] 上游 Gate（如有）的 decision status 为 `approved`
  - [ ] 当前 Gate 要求的所有成果物文件存在且版本号明确

### Step 2：运行前置校验

- **输入**：
  - `registers/` 目录下的全部 CSV 台账文件
  - `validators/scripts/validate_registers.py`
  - `validators/scripts/validate_traceability.py`
  - Reviewer findings 文件（来自 hw-review 产出）

- **操作**：
  1. **校验 1 — 台账完整性**：运行 `python validators/scripts/validate_registers.py`
     - 检查 exit code：0 = 全部 8 条规则通过，1 = 存在 blocker
     - 如失败，读取 stderr，逐条列出失败规则和详情
  2. **校验 2 — 追踪覆盖率**：运行 `python validators/scripts/validate_traceability.py`
     - 检查 exit code：0 = 覆盖率 ≥80%，1 = 覆盖率不足
     - 记录覆盖率和未追踪的 P0/P1 requirement 清单
  3. **校验 3 — Reviewer verdict 完整性**：
     - 列出当前 Gate 要求的全部成果物
     - 逐一检查每个成果物是否有 Reviewer verdict
     - verdict 必须为 `approved`、`conditional` 或 `rejected`，不得为 `pending`
     - 记录任何 `pending` 或缺失 verdict 的成果物
  4. **校验 4 — Blocker findings 检查**：
     - 汇总当前 Gate 全部成果物的 Reviewer findings
     - 统计 `severity=blocker` 且 `status!=resolved` 的 finding
     - 任一 blocker finding 未解决 → 校验不通过

- **检查点**：
  - [ ] validate_registers.py exit code = 0（全部 8 条规则通过）
  - [ ] validate_traceability.py exit code = 0（覆盖率 ≥80%）
  - [ ] 所有成果物的 reviewer verdict 不为 `pending`
  - [ ] 无未解决的 blocker finding

  如果任一校验失败：
  - 生成 **"Gate 阻断报告"**，逐项列出失败原因和修复建议
  - 停止 Gate 准备流程，等待问题修复后重新触发
  - **不进入** Step 3

### Step 3：收集和汇总 Reviewer Findings

- **输入**：
  - 当前 Gate 全部成果物的 Reviewer findings（来自 hw-review 产出，对齐 architecture.md 五.3 的 review-result 契约）
  - Review findings 中的 `severity`（blocker / high / medium / low）、`category`、`finding`、`required_action` 字段

- **操作**：
  1. 读取每个成果物对应的 Reviewer findings
  2. 按 severity 统计 finding 数量（blocker / high / medium / low）
  3. 按 category 统计 finding 分布（evidence / scope / requirement / acceptance / validation / risk / consistency）
  4. 提取 `required_action = submit_decision` 的 finding（需 PM 决策的事项）
  5. 列出所有 conditional approval 的条件项及其完成状态

- **检查点**：
  - [ ] 每个成果物的 finding 已完整读取
  - [ ] 按 severity 和 category 的统计数字准确
  - [ ] 需 PM 决策的 finding 全部列出
  - [ ] Conditional approval 条件逐一核对

### Step 4：编制 Gate 摘要

- **输入**：
  - Step 1 的 Gate 识别结果（gate_id, route, 成果物清单）
  - Step 2 的校验结果（4 项校验的通过/失败状态）
  - Step 3 的 Reviewer findings 汇总
  - 各成果物的摘要/关键结论（如有研究报告则提取摘要章节）
  - `registers/risks.csv` 中与该阶段相关的风险

- **操作**：
  1. 编写"阶段完成概况"章节：该阶段做了什么、产出了什么成果物、关键发现
  2. 编写"成果物与审查状态"表格：每项成果物的 ID/类型/版本/Reviewer verdict
  3. 编写"前置校验结果"章节：4 项校验的状态和关键数据
  4. 编写"需人工决策的事项"章节：从 Reviewer findings 和成果物中提取需要 PM 拍板的开放问题
  5. 编写"选项分析"章节：至少 2 个选项，每个选项含方案描述、优点、缺点、风险
  6. 编写"风险评估"章节：继续推进的风险 vs 不推进/暂停的风险
  7. 编写"Reviewer 审查摘要"章节：findings 总数、按 severity 和 category 分布、blocker/high 的详细列表
  8. 编写"Agent 建议"章节：明确标注"以下为 Agent 建议，最终决策权在人工 PM"，给出推荐选项及理由

- **检查点**：
  - [ ] 选项分析包含 ≥2 个真实选项，且"不通过/回退"为有效选项之一
  - [ ] 每个选项有独立的 pros/cons/risks 分析
  - [ ] Reviewer findings 统计数字与 Step 3 一致
  - [ ] 风险评估覆盖"推进"和"不推进"两个方向
  - [ ] Agent 建议明确标注非人工决策
  - [ ] 符合输出模板的完整章节结构（参见第 5 节）

### Step 5：生成 gate-request.json

- **输入**：
  - Step 1 的 Gate ID 和成果物清单
  - Step 2 的校验结果
  - `validators/schemas/gate-request.schema.json`

- **操作**：
  1. 构建 gate-request.json，字段对齐 schema：
     - `gate_id`：Gate1 ~ Gate7
     - `project_id`：从项目启动卡获取
     - `artifacts`：数组，每个元素含 artifact_id, artifact_type, version, review_verdict, content_hash（可选）
     - `validation_status.registers_check`：validate_registers.py 是否通过（boolean）
     - `validation_status.traceability_check`：validate_traceability.py 是否通过（boolean）
     - `decision_options`：从 Step 4 的选项分析中提取的选项标签列表
  2. 写入 `output/<project>/gate-<N>-request.json`
  3. 运行 `python validators/scripts/validate_gate.py output/<project>/gate-<N>-request.json` 验证
  4. 确认 exit code = 0

- **检查点**：
  - [ ] gate-request.json 所有 required 字段已填充
  - [ ] gate_id 符合 schema 的 enum 约束
  - [ ] 所有 artifact 的 review_verdict 为 approved / conditional / rejected
  - [ ] validate_gate.py 返回 READY（exit code 0）
  - [ ] 文件已写入 `output/<project>/gate-<N>-request.json`

### Step 6：呈现给人工 PM

- **输入**：
  - Step 4 的 Gate 摘要文档（完整 Markdown）
  - Step 5 的 gate-request.json

- **操作**：
  1. 将 Gate 摘要文档完整呈现给人工 PM，重点高亮：
     - 当前 Gate 和阶段
     - 选项分析章节（核心决策依据）
     - 风险评估章节（关键风险提示）
     - 前置校验状态
     - Reviewer 发现的 blocker/high finding（如有）
  2. 明确说明决策选项及其含义：
     - **批准（Approve）**：确认当前阶段产出，进入下一阶段
     - **退回（Reject）**：当前阶段产出不满足要求，需修正后重新提交
     - **有条件批准（Conditional Approve）**：在满足指定条件的前提下继续，条件完成后无需重新审批
  3. 等待人工 PM 的三选一回复

- **检查点**：
  - [ ] Gate 摘要已完整呈现
  - [ ] 决策选项已明确说明
  - [ ] 等待人工 PM 回复中（**此步骤尚未写入 decisions.csv**）

### Step 7：处理人工决策并写入 decisions.csv

- **输入**：
  - 人工 PM 的决策回复（approve / reject / conditional-approve）
  - 如为 conditional-approve，附带条件清单

- **操作**：
  1. **仅在人工 PM 明确回复后**执行以下操作：
     - 批准（Approve）：
       - 写入 decisions.csv：`decision_id = DEC-{project}-{seq}`, `decision = "Gate{N} approved"`, `decision_type = "gate"`, `status = "approved"`
       - 更新 Gate 摘要文档：在文档顶部追加"审批结果"章节，记录决策人、决策时间、决策结果
     - 退回（Reject）：
       - 写入 decisions.csv：`decision_id = DEC-{project}-{seq}`, `decision = "Gate{N} rejected — {退回原因}"`, `status = "rejected"`
       - 更新 Gate 摘要文档：记录退回原因
       - 通知人工 PM：根据退回原因修正后，需重新触发 hw-gate-prep
     - 有条件批准（Conditional Approve）：
       - 写入 decisions.csv：`decision_id = DEC-{project}-{seq}`, `decision = "Gate{N} conditional-approved — {条件摘要}"`, `status = "conditional"`
       - 更新 Gate 摘要文档：记录条件清单和完成期限
       - 将条件项写入 `notes` 字段
  2. 生成决策确认消息，回复人工 PM，包含：
     - decision_id
     - 决策结果
     - 下一步行动（进入下一阶段 / 修正后重新提交 / 按条件修改后继续）

- **检查点**：
  - [ ] decisions.csv 已写入且仅在人工 PM 回复**之后**写入
  - [ ] decision_id 格式为 `DEC-{project}-{seq}`（seq 为 decisions.csv 中已有最大序号 +1）
  - [ ] decision 字段包含 Gate 标识和决策结果
  - [ ] status 为 approved / rejected / conditional
  - [ ] Gate 摘要文档已更新审批结果
  - [ ] 人工 PM 已收到决策确认消息

## 5. Output Structure（输出结构）

### 输出文件

1. `output/<project>/gate-<N>-summary.md` — Gate 摘要文档
2. `output/<project>/gate-<N>-request.json` — Gate 审批请求（符合 gate-request.schema.json）
3. `registers/decisions.csv` — 新增一条 decision 记录（**仅在人工确认后**）

### Gate 摘要文档模板

以下为 `gate-<N>-summary.md` 的完整模板。所有 `{...}` 为变量占位符，由 Agent 在运行时填充。

```markdown
# Gate {N} 审批摘要 — {项目名称}

> 项目：{project_id}
> 路由：{L1/L2/L3}
> Gate 位置：{Gate 在流程中的位置描述，如"市场研究与用户研究完成后"}
> 生成时间：{YYYY-MM-DD HH:MM}
> 提交人：PM Agent (hw-gate-prep)

---

## 审批结果

> **此章节在人工 PM 决策后更新。**

| 字段 | 内容 |
|------|------|
| 决策人 | {人工 PM 姓名} |
| 决策时间 | {YYYY-MM-DD HH:MM} |
| 决策结果 | {批准 / 退回 / 有条件批准} |
| 决策 ID | {DEC-{project}-{seq}} |
| 条件/备注 | {如有条件批准，列出条件项；如退回，列出退回原因} |

---

## 一、阶段完成概况

### 本阶段产出

| 成果物 ID | 类型 | 版本 | 简述 |
|-----------|------|------|------|
| {ART-{project}-{seq}} | {成果物类型} | {v1.0} | {一句话描述} |

### 关键发现

1. {关键发现 1 — 对路由或产品方向有影响的发现}
2. {关键发现 2}
3. ...

### 阶段成果物文件清单

- `{文件路径 1}` — {说明}
- `{文件路径 2}` — {说明}
- ...

---

## 二、成果物与审查状态

| 成果物 ID | 类型 | 版本 | Reviewer Verdict | 备注 |
|-----------|------|------|------------------|------|
| {ART-001} | {market_study} | {v1.0} | {approved} | — |
| {ART-002} | {user_research} | {v1.0} | {approved} | — |

---

## 三、前置校验结果

| 校验项 | 脚本/方法 | 结果 | 详情 |
|--------|----------|------|------|
| 台账完整性 | `validate_registers.py` | {PASS / FAIL} | {8 条规则通过 N 条，失败 M 条} |
| 追踪覆盖率 | `validate_traceability.py` | {PASS — 85% / FAIL — 65%} | {覆盖 X/Y 条 P0/P1 requirement} |
| Reviewer verdict 完整性 | 人工逐项检查 | {PASS / FAIL} | {N 项成果物全部有 verdict / 缺失 M 项} |
| Blocker finding 检查 | 人工汇总 | {PASS / FAIL} | {无未解决 blocker / 存在 M 个未解决 blocker} |

> 如任一校验 FAIL，此 Gate 摘要不得提交审批。校验通过后方可进入下一步。

---

## 四、需人工决策的事项

以下事项需要人工 PM 在 Gate 审批时一并决策：

| # | 事项 | 来源 | 影响范围 | 建议 |
|---|------|------|---------|------|
| 1 | {事项描述} | {成果物 ID / Reviewer finding ID} | {影响的下游决策} | {Agent 建议} |
| 2 | ... | ... | ... | ... |

---

## 五、选项分析

### 选项 A：{批准 — 进入下一阶段}

**方案描述**：{确认当前阶段全部产出，Gate 通过，进入 {下一阶段名称}。}

**优点**：
1. {优点 1}
2. {优点 2}

**缺点**：
1. {缺点 1}
2. {缺点 2}

**风险**：
1. {风险 1 — 含严重程度和发生概率}
2. {风险 2}

---

### 选项 B：{退回 — 修正后重新提交}

**方案描述**：{当前阶段产出存在以下问题，需修正后重新提交 Gate 审批：{问题清单}。}

**优点**：
1. {优点 1 — 如"修正关键缺陷，降低下游返工风险"}
2. {优点 2}

**缺点**：
1. {缺点 1 — 如"额外耗时 X 天"}
2. {缺点 2}

**风险**：
1. {风险 1}
2. {风险 2}

**退回修正清单**：
- [ ] {修正项 1}
- [ ] {修正项 2}

---

### 选项 C：{有条件批准 / 终止 / 缩小范围}（可选）

{如果存在第三个真实选项，按上述格式填写。如果不存在，删除此章节。}

---

## 六、风险评估

### 继续推进的风险

| 风险 ID | 风险描述 | 严重程度 | 发生概率 | 当前缓解措施 | 残余风险 |
|---------|---------|---------|---------|-------------|---------|
| {RISK-{project}-{seq}} | {描述} | {高/中/低} | {高/中/低} | {措施} | {评估} |

### 不推进/暂停的风险

| # | 风险描述 | 影响 |
|---|---------|------|
| 1 | {如"错失市场窗口期"} | {具体影响量化} |
| 2 | {如"已有投入沉没"} | {已投入资源量} |

---

## 七、Reviewer 审查摘要

### 总体统计

| 指标 | 数值 |
|------|------|
| 审查成果物数 | {N} |
| Findings 总数 | {N} |
| Blocker | {N} |
| High | {N} |
| Medium | {N} |
| Low | {N} |

### 按 Category 分布

| Category | 数量 |
|----------|------|
| evidence | {N} |
| scope | {N} |
| requirement | {N} |
| acceptance | {N} |
| validation | {N} |
| risk | {N} |
| consistency | {N} |

### Blocker / High Finding 详情

| Finding ID | Severity | Category | 成果物 | 描述 | Required Action | 状态 |
|------------|----------|----------|--------|------|-----------------|------|
| {F-001} | {blocker} | {evidence} | {ART-001} | {描述} | {must_fix} | {resolved / unresolved} |

### Conditional Approval 条件追踪

| 成果物 | 条件 | 完成状态 |
|--------|------|---------|
| {ART-XXX} | {条件描述} | {已完成 / 未完成} |

---

## 八、Agent 建议

> **以下为 PM Agent 的分析建议，不具备决策权限。最终决策权在人工 PM。**

**推荐选项**：{选项 A / B / C}

**推荐理由**：
1. {理由 1}
2. {理由 2}

**关键假设**（如果这些假设不成立，建议可能改变）：
1. {假设 1}
2. {假设 2}

**什么新证据会改变这个建议**：
- {如果出现 X → 应改为选项 Y}
- {如果出现 Z → 应改为选项 B}
```

### gate-request.json 模板

```json
{
  "gate_id": "{Gate1 ~ Gate7}",
  "project_id": "{project_id}",
  "artifacts": [
    {
      "artifact_id": "ART-{project}-{seq}",
      "artifact_type": "{成果物类型}",
      "version": "{v1.0}",
      "review_verdict": "{approved | conditional | rejected}"
    }
  ],
  "validation_status": {
    "registers_check": true,
    "traceability_check": true
  },
  "decision_options": [
    "批准 — 进入下一阶段",
    "退回 — 修正后重新提交",
    "有条件批准 — {条件摘要}"
  ]
}
```

### decisions.csv 写入记录

在人工 PM 确认决策后，向 `registers/decisions.csv` 追加一条记录。字段对齐现有 decisions.csv 结构：

| 字段 | 值 | 说明 |
|------|---|------|
| decision_id | `DEC-{project}-{seq}` | seq 为已有最大序号 +1 |
| decision | `Gate{N} {approved / rejected / conditional-approved} — {摘要}` | 含 Gate 标识和决策 |
| decision_type | `gate` | 固定值 |
| date | `{YYYY-MM-DD}` | 决策日期 |
| owner | `{人工 PM 姓名}` | 决策人 |
| options_considered | `{选项A / 选项B / 选项C}` | 本次 Gate 考虑的全部选项 |
| rationale | `{决策理由摘要}` | 人工 PM 提供的决策理由 |
| related_evidence | `{关联的 evidence_id，逗号分隔}` | 支撑决策的关键证据 |
| status | `{approved / rejected / conditional}` | 决策状态 |
| notes | `{备注信息}` | 如为 conditional-approve，列出条件项 |

## 6. Quality Bar（最低质量标准）

提交前，PM Agent 自检以下所有项。Reviewer 将按此 checklist 逐项检查。

- [ ] Gate ID 与 AGENTS.md 第 6 节 Gate 位置表完全一致，且在当前路由（L1/L2/L3）范围内
- [ ] 4 项前置校验全部 PASS：validate_registers.py (exit 0)、validate_traceability.py (exit 0)、所有成果物 verdict 不为 pending、无未解决 blocker finding
- [ ] 选项分析包含 ≥2 个真实选项，每个选项有独立的 pros/cons/risks，且"不通过/回退"为有效选项
- [ ] Reviewer findings 统计数字准确：总数、按 severity 分布、按 category 分布均可用原始 findings 文件逐条验证
- [ ] gate-request.json 通过 validate_gate.py 验证（exit 0），所有 required 字段已填充
- [ ] Gate 摘要文档的"审批结果"章节在人工 PM 决策前保持空白，仅在决策后填写
- [ ] decisions.csv 的写入时间严格在人工 PM 回复之后（可通过文件修改时间戳验证）
- [ ] decision_id 格式为 `DEC-{project}-{seq}`，seq 连续不跳号，不与已有 ID 重复
- [ ] 风险评估覆盖"继续推进"和"不推进"两个方向，每个风险有关联的 mitigation 或说明
- [ ] 无占位符残留（TBD、TODO、"待补充"、"根据实际情况调整"等）

## 7. Tool Integration（工具链）

### 主工具链

| 工具 | 用途 | 调用方式 | 成功标准 |
|------|------|---------|---------|
| `validate_registers.py` | 台账 8 条完整性校验 | `python validators/scripts/validate_registers.py` | exit code 0 |
| `validate_traceability.py` | P0/P1 追踪覆盖率校验 | `python validators/scripts/validate_traceability.py` | exit code 0（覆盖率 ≥80%） |
| `validate_gate.py` | gate-request.json 条件校验 | `python validators/scripts/validate_gate.py <path/to/gate-request.json>` | exit code 0（READY） |
| Bash | 文件存在性检查、读取 CSV | `ls`, `cat`, `head -1` | 文件存在且可读 |
| Read | 读取成果物摘要、Reviewer findings、registers CSV | Read tool | 内容可解析 |
| Write | 写入 Gate 摘要文档、gate-request.json | Write tool | 文件写入成功 |
| Bash（append） | 追加 decisions.csv 记录 | `echo` 追加或 Python csv 追加 | 记录追加成功，ID 不重复 |

### 降级链

| 场景 | 主方案 | 降级方案 |
|------|--------|---------|
| validate_registers.py 不可用（环境问题） | 运行脚本 | 人工逐条对照 8 条规则检查 CSV，但在 Gate 摘要中标注"手动校验" |
| validate_traceability.py 不可用 | 运行脚本 | 读取 requirements.csv 和 traceability.csv，人工计算覆盖率 |
| CSV 文件为空（项目早期阶段） | 脚本正常处理空文件 | 记录"无数据"并在校验结果中标注为 PASS（空集合平凡满足条件） |
| Reviewer findings 文件缺失 | 中止 Gate 准备 | 通知人工 PM：成果物尚未通过 Reviewer 审查 |

### 工具使用的边界

- **Python 脚本**：仅用于确定性校验（8 条规则、覆盖率、Gate 条件），不做语义分析或质量判断
- **Read 工具**：用于读取结构化文件（CSV、Markdown、JSON），不用于读取二进制文件
- **Write 工具**：仅用于写入 Gate 摘要文档和 gate-request.json。decisions.csv 的写入使用 Bash echo 追加以确保格式一致性
- **禁止**：不允许 Agent 手动修改 CSV 内容以通过校验（如手动删除未通过记录、修改 verdict 字段等）

## 8. Best Practices（最佳实践）

### 好的输出示例

#### Gate 摘要中的选项分析

```markdown
### 选项 A：批准 — 进入竞品分析

方案描述：确认市场研究和用户研究产出充分，Gate 2 通过，进入竞品分析阶段。

优点：
1. 研究覆盖了目标市场的 TAM/SAM/SOM 估算，数据来源 A/B 级，置信度高
2. 用户研究识别了 3 个核心 JTBD，可作为竞品分析的对比维度

缺点：
1. 用户研究样本偏向一线城市，三四线城市覆盖不足
2. 合规研究（L2+ 需要）尚未启动，到 Gate 4 前需要补充

风险：
1. 三四线城市用户需求可能显著不同 → 如后续发现偏差，需回补用户研究（影响：中等，概率：低）
2. 竞品分析可能发现市场研究遗漏的竞品 → 需在 Gate 3 决策是否回补（影响：低，概率：中）

### 选项 B：退回 — 补充三四线城市用户研究

方案描述：当前用户研究样本地域覆盖不均衡，退回 Researcher 补充三四线城市用户访谈后再重新提交 Gate 2。

优点：
1. 在竞品分析前补齐用户洞察的地域覆盖，避免后期返工
2. 三四线城市可能揭示不同的价格敏感度和渠道偏好

缺点：
1. 额外耗时 5-7 天（招募 + 访谈 + 分析）
2. 此阶段竞品分析可以先行启动（与用户研究并行），退回会阻塞竞品分析

风险：
1. 延迟可能导致竞品先发 → 5-7 天在智能硬件领域窗口期影响有限（影响：低，概率：低）

退回修正清单：
- [ ] 补充 ≥5 个三四线城市用户访谈
- [ ] 更新用户研究报告的地域覆盖分析章节
- [ ] 重新提交 Reviewer 审查
```

### 常见陷阱

| 陷阱 | 错误做法 | 正确做法 |
|------|---------|---------|
| 过早写入 decisions.csv | 生成 Gate 摘要时顺便写一条"待审批"的 decision 记录 | 仅在人工 PM 回复后写入。Gate 准备阶段不碰 decisions.csv |
| 跳过 blocker finding | Reviewer 标注了 blocker，但 PM Agent 认为"问题不大"就提交 Gate | blocker finding 必须 resolved 才能提交 Gate。如对 severity 有异议，与 Reviewer 沟通后由 Reviewer 更新 finding |
| 选项分析流于形式 | "选项 A: 批准" / "选项 B: 不批准（不推荐）" | 每个选项独立分析。不推荐的选项也要客观列出其优点和适用场景 |
| Gate 识别错误 | L2 项目在 Gate 3 后直接跳到 Gate 5（跳过 Gate 4 产品规划） | 严格按 Gate 序列，不允许跳 Gate。中间 Gate 不可跳过 |
| 校验失败仍提交 | validate_traceability.py 返回 FAIL 但手动改 gate-request.json 的 validation_status 为 true | 校验失败 = Gate 阻断。修复问题后重新校验 |
| 忽略 conditional approval 的条件 | 上一个 Gate 是有条件批准，但未检查条件是否满足就准备当前 Gate | 在 Gate 摘要中明确列出上一个 Gate 的条件项及其完成状态 |

## 9. Further Reading（扩展阅读）

### 关联模板
- `templates/00_项目启动卡.md` — 项目 ID、路由判定的来源
- `templates/00A_文档关系与追踪说明.md` — 成果物之间的输入输出依赖关系

### 关联台账
- `registers/decisions.csv` — 本 Skill 写入的台账文件。写入时机：**人工确认后**
- `registers/risks.csv` — Gate 风险评估的输入来源
- `registers/evidence.csv` — 支撑决策的证据链
- `registers/traceability.csv` — 追踪覆盖率校验的输入
- `registers/requirements.csv` — P0/P1 覆盖率校验的输入

### 关联校验脚本
- `validators/scripts/validate_registers.py` — 台账完整性 8 条规则。Gate 前置校验第 1 项
- `validators/scripts/validate_traceability.py` — P0/P1 追踪覆盖率（阈值 80%）。Gate 前置校验第 2 项
- `validators/scripts/validate_gate.py` — gate-request.json 的条件校验。Step 5 使用
- `validators/schemas/gate-request.schema.json` — gate-request.json 的 JSON Schema 定义

### 方法论参考
- `docs/architecture.md` 第二章（完整流程与人工门径）— Gate 在整体流程中的位置
- `docs/architecture.md` 第五章（Agent 通信协议）— Researcher → PM、PM → Reviewer、Reviewer → PM 的契约格式
- `docs/architecture.md` 第十三章（pm-skills 方法论参考）— 阶段审计模板和市场研究方法论
- `AGENTS.md` 第 6 节（人工门径规则）— Gate 位置、条件、审批流程的权威定义

### 关联 Skills
- `hw-intake` — 上游 Skill，Gate 1 的来源。产出路由判定和任务包
- `hw-review` — 上游 Skill，产出的 Reviewer findings 是本 Skill 的核心输入
- `hw-market-study` — 上游 Skill（Gate 2），产出市场研究报告
- `hw-user-research` — 上游 Skill（Gate 2），产出用户研究报告
- `hw-competitive-analysis` — 上游 Skill（Gate 3），产出竞品分析报告
- `hw-product-strategy` — 上游 Skill（Gate 4），产出产品规划报告
- `hw-mrd-brd` — 上游 Skill（Gate 5），产出 MRD/BRD
- `hw-product-definition` — 上游 Skill（Gate 6），产出产品定义文档
- `hw-prd` — 上游 Skill（Gate 7），产出 PRD + requirements.csv
- `hw-validation-plan` — 上游 Skill（Gate 7），产出验证计划
- `hw-retro` — 下游 Skill，项目复盘时读取 decisions.csv 中的决策链
