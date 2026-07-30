---
name: hw-validation-plan
description: >
  生成智能硬件验证计划。触发条件：PRD 已批准、assumptions.csv 和 risks.csv 就绪。
  输入已批准的 PRD + 假设表 + 风险表，输出验证计划文档 + traceability.csv 增量更新。
  适用场景：PM Agent 在 PRD Gate 通过后进入验证规划阶段。
---

# HW Validation Plan — 验证计划生成

## 1. Purpose（目的）

本 Skill 解决"如何验证产品定义和 PRD 中的关键假设、功能、性能、可靠性、合规性和量产可行性"的问题。在 Agent 工作流中位于 PM 规划阶段的最后一步，承接已批准的 PRD，产出验证计划文档，为 Gate 7（PRD + 验证计划审批）提供输入。

核心任务：
- 从未经验证的高置信度假设中提取需要优先验证的关键项
- 为高影响风险设计缓解效果验证方案
- 确保每个 P0/P1 需求有对应的验证项
- 维护 traceability.csv，完成 requirement → validation_item 的追踪链条

## 2. Context（上下文/适用场景）

### 触发条件
- PRD（PRD_产品需求文档.md）已通过 Reviewer 审查并获得人工 Gate 批准
- `registers/assumptions.csv` 中存在 confidence=高 的记录
- `registers/risks.csv` 中存在需要验证缓解效果的风险记录
- `registers/requirements.csv`（由 hw-prd 产出）中 P0/P1 需求已确定

### 前置条件（Gate）
- Gate 6（产品定义审批）已通过
- PRD 文档已冻结（状态：approved）
- Reviewer findings 中无 severity=blocker 的未解决问题

### 输出消费者
- **Gate 7 审批人**（人类 PM）：审阅验证计划的充分性和可执行性
- **hw-gate-prep**：生成 Gate 7 摘要简报
- **hw-review**：对照验证计划审查执行结果
- **hw-retro**：复盘时引用验证结果和方法有效性

## 3. Operating Principles（操作原则）

### 原则 1：先验证影响大的，再验证容易验证的
验证资源有限，优先级排序：高置信度假设（可能成为 blocker）> 高影响风险缓解 > P0 需求 > P1 需求。
- **不要**对所有假设平均用力，或者从最容易验证的项开始。
- 违反后果：关键假设未及时验证，在后期发现推翻基础前提，返工成本指数级上升。

### 原则 2：每个验证项必须有可量化、可复现的通过标准
"功能正常"不是通过标准。通过标准必须是数值阈值、二值判定条件、或可观测的行为描述。
- **不要**使用"满足用户需求""体验良好""稳定运行"等不可测量的表述作为唯一通过标准。
- 违反后果：验证执行者无法判断是否通过，验证结果无决策价值。

### 原则 3：验证方法必须匹配验证对象的类型
bench test 对应性能和功能、field test 对应真实环境、certification test 对应合规、user trial 对应用户价值、supplier audit 对应供应链、reliability test 对应寿命和耐久。
- **不要**用单一验证方法覆盖所有验证对象（如全部用 bench test 代替 field test）。
- 违反后果：实验室通过的项在真实场景中失效，或者合规项在生产前才发现不通过。

### 原则 4：未关闭的高影响项是进入下一阶段的 blocker
验证计划产出的风险关闭清单中，任何 status≠closed 的高影响项必须在 Gate 7 摘要中显式列出，作为"条件性批准"的前置条件。
- **不要**在风险关闭清单中将未验证的风险标记为"低风险"以绕过 Gate 检查。
- 违反后果：带着未验证的高风险进入开发阶段，量产时才暴露问题。

### 原则 5：验证项与需求和证据的双向可追溯
每条验证项必须通过 traceability.csv 关联到至少一条 requirement，理想情况下也关联到支撑该需求的 evidence。
- **不要**产出一个孤立的验证计划文档，验证项与需求和假设之间没有显式 ID 关联。
- 违反后果：验证执行后无法判断"我们验证了什么、对应什么需求"，也无法评估需求覆盖率。

## 4. Instructions（分步骤指引）

### Step 1: 加载项目上下文与输入文件

- **输入**：
  - `PRD_产品需求文档.md` — 提取产品名称、目标市场、P0/P1 需求列表
  - `registers/assumptions.csv` — 加载全部假设记录
  - `registers/risks.csv` — 加载全部风险记录
  - `registers/requirements.csv` — 加载全部需求记录，过滤 P0 和 P1
  - `registers/traceability.csv` — 加载当前追踪状态，识别已有的 evidence→requirement 关联
- **操作**：
  1. 解析 PRD 文档，提取产品名称（用于 project 缩写）和所有 P0/P1 需求 ID
  2. 用 Python/工具读取三个 CSV 文件到 DataFrame，验证字段完整性
  3. 在 assumptions.csv 中筛选 `confidence=高` 的记录
  4. 在 risks.csv 中筛选 `probability=高` 或 `impact=高` 的记录
  5. 在 traceability.csv 中确认哪些 requirement_id 已有 evidence_id 关联
- **检查点**：
  - [ ] 产品名称已提取，project 缩写可用于生成 VI-{project}-{seq} ID
  - [ ] P0/P1 requirement_id 列表已获取（≥1 条）
  - [ ] assumptions.csv 中 confidence=高 的记录已定位
  - [ ] risks.csv 中高概率/高影响记录已定位

### Step 2: 提取需要验证的关键假设

- **输入**：Step 1 筛选出的 confidence=高 的假设记录
- **操作**：
  1. 遍历每条高置信度假设，检查 `validation_method` 字段：
     - 若 `validation_method` 为空 → 标记为"待验证"，需设计验证方法
     - 若 `validation_method` 非空 → 已有验证方法，检查该方法是否仍适用（方法可执行性判断）
  2. 对每条"待验证"的假设，按 impact 字段从高到低排序
  3. 确定验证优先级：impact=高 且 category=技术/供应链 → P0；其余 → P1
  4. 为每条假设生成验证项 ID：`VI-{project}-{seq}`
  5. 准备假设验证表（填充到输出模板第 2 节）
- **检查点**：
  - [ ] 所有 confidence=高 且 validation_method 为空的假设都有对应的验证项
  - [ ] 验证项按 impact 降序排列，高影响优先
  - [ ] VI ID 与项目缩写一致，序列号不重复

### Step 3: 提取需要验证缓解效果的高影响风险

- **输入**：Step 1 筛选出的 probability=高 或 impact=高 的风险记录
- **操作**：
  1. 检查每条高影响/高概率风险的 `mitigation` 字段：
     - 若 `mitigation` 为空 → 标记为"无缓解措施"，需要优先处理（提出缓解建议 + 验证方案）
     - 若 `mitigation` 非空 → 需要验证缓解措施是否有效
  2. 设计验证方法验证缓解措施的有效性（如：风险触发条件模拟测试、缓解措施效果量化对比）
  3. 为每条风险项生成风险关闭条目（填充到输出模板第 8 节），包含验证结果（初始状态为空，待执行后回填）
- **检查点**：
  - [ ] 所有 probability=高 或 impact=高 的风险在风险关闭清单中有对应条目
  - [ ] 有 mitigation 的风险有对应的缓解效果验证方法
  - [ ] 无 mitigation 的风险已标记为"需优先确定缓解措施"

### Step 4: 映射 P0/P1 需求到验证项

- **输入**：Step 1 的 P0/P1 requirement_id 列表 + PRD 文档中的验收标准
- **操作**：
  1. 遍历每个 P0 和 P1 需求，从 PRD 中提取该需求的验收标准（Acceptance Criteria）
  2. 将验收标准转化为可测试的验证项：
     - 功能需求 → 功能验证表（输出模板第 3 节）
     - 性能/可靠性需求 → 性能与可靠性验证表（输出模板第 4 节）
     - 合规需求 → 认证与合规验证表（输出模板第 5 节）
  3. 为每个验证项分配验证方法类型（bench test / field test / certification test / user trial / supplier audit / reliability test）
  4. 确定每个验证项的样本量和责任人（如能从 PRD 中推断）
  5. 为每个验证项生成 VI ID
- **检查点**：
  - [ ] 每个 P0 需求在功能验证表中 ≥1 条验证项
  - [ ] 每个 P1 需求在功能验证表中 ≥1 条验证项
  - [ ] 验证方法类型与实际验证对象匹配（功能测试≠可靠性测试）

### Step 5: 设计验证方法与参数

- **输入**：Step 2/3/4 汇总的所有验证项
- **操作**：
  1. 按验证方法类型分组：
     - **bench test**（台架测试）：定义测试环境、仪器、测试步骤、数据采集方式
     - **field test**（现场测试）：定义测试场景、环境条件、时长、观测指标
     - **certification test**（认证测试）：引用具体标准编号（如 CCC/CE/FCC）、当前认证状态
     - **user trial**（用户试用）：定义用户数量、任务、观察指标、NPS/满意度阈值
     - **supplier audit**（供应商审核）：定义审核清单、关键物料、准入标准
     - **reliability test**（可靠性测试）：定义样本量、加速因子、测试时长、失效判定标准
  2. 对每种方法类型，填充对应的输出模板章节
  3. 确认认证合规项（第 5 节）中列出的标准/法规与目标市场对齐（参考 PRD 中的目标市场信息）
- **检查点**：
  - [ ] 每种验证方法类型的关键参数已定义（不能留空）
  - [ ] 涉及认证的标准编号已填写（不能写"待定"或"后续确认"）
  - [ ] 样本量和通过标准已设定

### Step 6: 更新 traceability.csv

- **输入**：Step 2/3/4 生成的所有验证项及其 VI ID
- **操作**：
  1. 对于每条验证项，确定其关联的 requirement_id：
     - 假设验证项 → 关联该假设影响的 requirement（从 PRD 推断或从 existing traceability 查找）
     - 风险验证项 → 关联该风险影响的 requirement
     - 功能验证项 → 直接关联对应的 requirement_id
  2. 在 traceability.csv 中**增量追加**新行：
     - 若该 requirement_id 已有 traceability 记录且 validation_item 为空 → 更新 validation_item 字段
     - 若该 requirement_id 尚无 traceability 记录 → 新增一行
     - 按 AGENTS.md 规则，traceability 写入时机为"增量追加"
  3. 生成 trace_id 格式：`T-{project}-{seq}`
  4. 每条新记录至少填写：`trace_id`, `requirement_id`, `validation_item`
  5. 验证引用完整性：所有 requirement_id 必须在 requirements.csv 中存在
- **检查点**：
  - [ ] 所有新验证项已通过 validation_item 字段关联到至少一条 requirement
  - [ ] 无孤儿引用：引用的 requirement_id 在 requirements.csv 中存在
  - [ ] trace_id 序列不重复

### Step 7: 编写验证计划文档

- **输入**：Step 2~6 的所有产物（验证项表格 + traceability 更新内容）
- **操作**：
  1. 按输出模板（见第 5 节）的 8 个章节结构组织文档
  2. 将 Step 2 产出的假设验证表填入第 2 节
  3. 将 Step 4 产出的功能验证表填入第 3 节
  4. 将 Step 5 产出的性能/可靠性/认证/试产/用户验证表分别填入第 4/5/6/7 节
  5. 将 Step 3 产出的风险关闭清单填入第 8 节
  6. 编写第 1 节"验证目标"摘要，明确：
     - 验证阶段（由路由等级决定：L1 → EVT+DVT, L2 → EVT+DVT+PVT, L3 → 全阶段）
     - 验证范围和不在范围的内容
     - 总体通过标准
  7. 文件命名为 `{project}_验证计划.md`，存放于项目 output 目录
- **检查点**：
  - [ ] 8 个章节全部存在，无空表（至少有一条数据）
  - [ ] 第 1 节验证阶段与项目路由等级对齐
  - [ ] 所有表格的列名与模板一致，无自定义额外列

## 5. Output Structure（输出结构）

### 输出文件清单

1. **`output/{project}/06_验证计划.md`** — 验证计划完整文档
2. **`registers/traceability.csv`** — 增量追加 requirement → validation_item 关联记录
3. **`registers/assumptions.csv`** — 更新 validation_method 字段（对 Step 2 中补充了验证方法的假设）

### 验证计划文档完整模板

```markdown
# 06_验证计划 — {产品名称}

> 版本: 1.0 | 日期: {生成日期} | 项目: {project} | 路由: L{1|2|3}

## 1. 验证目标

### 说明
本验证计划用于确认产品定义和 PRD 中的关键假设、功能、性能、可靠性、合规和量产可行性。智能硬件验证覆盖 EVT、DVT、PVT 及用户验证。

| 项目 | 内容 |
|------|------|
| 验证阶段 | {概念验证 / EVT / DVT / PVT / 小批量 / 上市后} |
| 验证目标 | {本阶段要验证什么——一句话总结} |
| 验证范围 | {列出在范围内的验证类型} |
| 不验证范围 | {列出明确不在范围内的验证类型及原因} |
| 通过标准 | {整体通过标准——所有P0验证项通过 + 高影响风险关闭 + 无Blocker级别未解决问题} |

## 2. 关键假设验证

| 假设编号 | 假设内容 | 风险等级 | 验证方式 | 通过标准 | 失败处理 |
|----------|----------|----------|----------|----------|----------|
| A-{project}-001 | {假设原文} | 高/中/低 | {bench test / field test / user trial / supplier audit} | {可量化的通过标准} | {假设被推翻后的处理方案} |

## 3. 功能验证

| 需求编号 | 测试项 | 测试方法 | 样本量 | 通过标准 | 负责人 |
|----------|--------|----------|--------|----------|--------|
| REQ-{project}-001 | {测试项描述} | {bench test / field test / user trial} | {N}台 | {可量化的通过标准} | {角色/团队} |

## 4. 性能与可靠性验证

| 测试项 | 条件 | 样本量 | 目标值 | 通过标准 | 备注 |
|--------|------|--------|--------|----------|------|
| 功耗 | {工作模式 + 电压} | {N}台 | {目标功耗值} | {容许偏差范围} | |
| 连接稳定性 | {协议 + 距离 + 干扰条件} | {N}台 | {目标值} | {断连次数/时长上限} | |
| 老化 | {温度 + 湿度 + 时长} | {N}台 | {MTBF目标} | {失效判定标准} | |
| 环境适应性 | {温度范围 + 湿度 + 振动/跌落} | {N}台 | {目标值} | {通过标准} | |

## 5. 认证与合规验证

| 合规项 | 适用原因 | 标准/法规 | 当前状态 | 负责人 | 截止时间 |
|--------|----------|-----------|----------|--------|----------|
| {认证名称，如CCC} | {目标市场：中国大陆，产品类型：智能硬件} | {标准编号，如 GB 4943.1-2022} | 未评估 / 进行中 / 通过 / 不适用 | {角色} | {YYYY-MM-DD} |

## 6. 试产与量产验证

| 项目 | 内容 |
|------|------|
| 试产批次 | {批次数量和每批数量} |
| 样本数量 | {总样本量} |
| 良率目标 | {百分比，如 ≥95%} |
| 关键工艺 | {列出需要重点验证的工艺环节} |
| 关键物料 | {列出长交期/高风险物料} |
| 问题关闭标准 | {如：所有severity=critical问题关闭，major问题有处理方案} |

## 7. 用户验证

| 验证对象 | 用户数量 | 任务 | 观察指标 | 通过标准 |
|----------|----------|------|----------|----------|
| {验证的场景或功能} | {N}人 | {用户需要执行的具体任务} | {量化指标，如任务完成率、NPS、满意度评分} | {可量化的通过阈值} |

## 8. 风险关闭清单

| 风险编号 | 风险描述 | 验证结果 | 是否关闭 | 后续动作 |
|----------|----------|----------|----------|----------|
| RISK-{project}-001 | {风险原文} | {验证执行后回填} | 是/否 | {未关闭的后续处理方案} |
```

### traceability.csv 新增记录格式

```csv
trace_id,research_finding,market_need,product_definition,requirement_id,validation_item,evidence_id,status,notes
T-{project}-{seq},,{市场需要描述},,REQ-{project}-{seq},VI-{project}-{seq},EV-{project}-{seq},active,验证计划阶段追加
```

- `validation_item` 填写格式：`VI-{project}-{seq}`，对应验证计划中的验证项 ID
- 若该 requirement 在 research 阶段已有 evidence 关联，填入 `evidence_id`；否则留空
- `status` 统一填 `active`

### assumptions.csv 回写格式

对 Step 2 中补充了验证方法的高置信度假设，更新 `validation_method` 字段：

```csv
A-{project}-001,{假设原文},{category},{related_doc},{impact},高,{新设计的验证方法},{owner},待验证,验证计划阶段补充验证方法
```

## 6. Quality Bar（最低质量标准）

验证计划产出必须通过以下 checklist：

- [ ] **假设覆盖率**：assumptions.csv 中所有 confidence=高 且 validation_method 为空的假设，在验证计划第 2 节中有对验证项（覆盖率 100%）
- [ ] **风险覆盖率**：risks.csv 中所有 probability=高 或 impact=高 的风险，在验证计划第 8 节中有对应条目（覆盖率 100%）
- [ ] **需求覆盖率**：requirements.csv 中所有 P0 和 P1 需求，在验证计划第 3 节（或第 4 节）中有 ≥1 条对应验证项（覆盖率 100%）
- [ ] **通过标准可量化**：每一条验证项的"通过标准"字段包含具体的数值阈值或布尔判定条件；不包含模糊表述（"正常""良好""满意""稳定"）
- [ ] **验证方法类型正确**：每条验证项的验证方法与验证对象匹配——功能项用 bench/field test，合规项用 certification test，用户价值项用 user trial，供应链项用 supplier audit，寿命项用 reliability test
- [ ] **traceability 完整**：traceability.csv 中所有 VI-{project} 开头的 validation_item 都有对应的 requirement_id，且该 requirement 在 requirements.csv 中存在
- [ ] **认证标准具体**：第 5 节中所有合规项的"标准/法规"列填写了具体标准编号（如 GB 4943.1-2022），不能出现"待定""后续确认""TBD"
- [ ] **无占位符**：全文不包含 TBD、TODO、"根据实际情况调整"等占位符文本

## 7. Tool Integration（工具链）

### 主要工具

| 工具 | 用途 | 使用边界 |
|------|------|---------|
| Python (pandas) | 读取和操作 assumptions.csv / risks.csv / requirements.csv / traceability.csv | 仅用于数据读取、筛选、验证引用完整性。不用于生成验证计划正文。 |
| 文件读写 (Read/Write) | 读取 PRD 和输入文件，写入验证计划文档 | 写入前确认目标目录存在 |
| CSV 追加 (Edit/Write) | 增量追加 traceability.csv 记录 | 仅追加新行，不修改已有记录的 evidence_id 或 requirement_id |

### 降级链

| 场景 | 主方案 | 降级方案 |
|------|--------|---------|
| Python 不可用 | 用 pandas 读取 CSV | 用 Bash `csvkit`（csvcut, csvgrep）或逐行解析 |
| PRD 文档不可解析 | 直接读取 Markdown 结构 | 要求用户提供 P0/P1 requirement_id 列表 |
| assumptions.csv 为空 | 正常流程（无假设验证项） | 跳过第 2 节，在验证目标中注明"本产品无高置信度未验证假设" |

### 质量门禁阈值

- P0 需求验证覆盖率必须 = 100%（< 100% 不允许进入 Gate 7）
- P1 需求验证覆盖率 ≥ 90%（< 90% 需在验证目标中说明原因）
- assumptions 验证覆盖率必须 = 100%（高置信度 + 无验证方法的假设全部覆盖）

## 8. Best Practices（最佳实践）

### 好的输出 vs 差的输出

**好的假设验证项：**
```
| A-CWLS-003 | 用户愿意为AI功能额外付费$5/月 | 高 | user trial: 100人盲测，对比AI版vs基础版选择率 | AI版选择率 ≥30% 且愿意付费比例 ≥20% | 若未通过，降级AI为可选功能，基础版先行上市 |
```

**差的假设验证项：**
```
| A-CWLS-003 | 用户愿意为AI功能额外付费$5/月 | 高 | 用户调研 | 用户反馈良好 | 调整定价 |
```
问题：验证方法模糊（用户调研没有样本量和方案）、通过标准不可量化（"良好"）、失败处理不具体。

**好的功能验证项：**
```
| REQ-CWLS-012 | 设备从待机唤醒到全功能就绪的响应时间 | bench test: 用示波器测量GPIO唤醒信号到主循环就绪的时间差，N=10台，每台测20次 | N=10台 | 平均值 ≤200ms，P99 ≤500ms | 固件工程师 |
```

**差的功能验证项：**
```
| REQ-CWLS-012 | 唤醒响应速度 | 测试 | 若干台 | 响应快 | 开发 |
```
问题：无具体测试方法、样本量模糊、通过标准不可测量、责任人不明确。

### 常见陷阱

1. **把验收标准直接复制为验证项**：验收标准描述"是什么"，验证项描述"怎么测"。必须增加测试方法、样本量、通过标准。
2. **忽略认证的前置时间**：CCC/CE/FCC 认证通常需要 4~12 周，必须在验证计划中标注截止时间，倒推到项目计划中。
3. **user trial 只测功能不测价值**：用户验证不仅要看"能不能用"，还要看"愿不愿用、愿不愿付钱"。观察指标必须包含行为数据（选择率、留存率、付费意愿），不能只有满意度问卷。
4. **风险关闭清单留空**：初始状态下"验证结果"列可以为空（待执行后回填），但"是否关闭"和"后续动作"必须填写当前状态和预期关闭路径。

## 9. Further Reading（扩展阅读）

### 关联模板
- `06_验证计划.md` — 验证计划输出模板（本文档第 5 节已包含完整模板）
- `PRD_产品需求文档.md` — PRD 模板，包含验收标准定义
- `04_产品定义文档.md` — 产品定义模板，包含关键假设来源

### 关联台账
- `registers/assumptions.csv` — 假设表（输入：提取待验证假设；输出：回写 validation_method）
- `registers/risks.csv` — 风险表（输入：提取高影响风险）
- `registers/requirements.csv` — 需求表（输入：提取 P0/P1 需求）
- `registers/traceability.csv` — 追踪矩阵（输出：增量追加 validation_item 关联）
- `registers/evidence.csv` — 证据表（输入：关联已有 evidence_id 到验证项）

### 关联 Skills
- **hw-prd**（上游）：产出 PRD + requirements.csv，是本 Skill 的主要输入
- **hw-gate-prep**（下游）：使用本 Skill 产出的验证计划生成 Gate 7 摘要
- **hw-review**（下游）：对照验证计划审查执行结果
- **hw-retro**（下游）：复盘时引用验证方法有效性评估

### 方法论参考
- AGENTS.md 第 4 节"技能路由表"：验证计划在工作流中的位置
- AGENTS.md 第 5 节"台账规则"：traceability.csv 的写入时机和 ID 格式约定
- AGENTS.md 第 6 节"人工门径规则"：Gate 7 的通过条件（PRD + 验证计划 + Reviewer 通过）
