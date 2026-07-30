---
name: hw-review
description: >
  Reviewer Agent 独立审查 Skill。当 Researcher 产出研究报告 draft 或 PM 产出产品文档 draft 时触发。
  输入为待审文档 + 关联 CSV 台账，输出为结构化 findings（带 severity + category + required_action）。
  实施 3-Lens 对抗性验证方法论，对 C 级源的高风险声明进行系统化核验。
  不修改文档，不替代 PM 决策。
---

# hw-review — 独立审查

## 1. Purpose（目的）

本 Skill 实现 Reviewer Agent 的核心职责：**独立审查 Researcher 和 PM 的所有产出，回答"做得对吗？"**。

在 3-Agent 协作系统中的位置：

```
Researcher/PM 产出 draft → hw-review 独立审查 → findings 返回 PM
                                                → 通过后进入 Gate 审批
```

本 Skill 的输出是 Gate 审批的前置条件 —— 未经 Reviewer 通过的文档不得进入 Gate。

## 2. Context（上下文/适用场景）

### 触发条件

- Researcher 完成研究报告 draft（market_study / user_research / competitive_analysis / compliance_research / patent_analysis）
- PM 完成产品文档 draft（product_strategy / mrd / brd / product_definition / prd / validation_plan）
- PM 发起显式审查请求，附带 `review-request` YAML

### 前置条件

- 待审文档已产出 draft 版本（maturity: draft）
- 关联 CSV 台账可访问（evidence.csv 至少存在；PRD 审查还需 requirements.csv + traceability.csv）
- review-request 中声明的 input_artifacts 均已就绪

### 输出消费者

- PM Agent：根据 findings 修正文档
- hw-gate-prep：汇总 findings 生成 Gate 摘要
- 人类 PM：在 Gate 审批时参考 Reviewer 意见
- risks.csv：如审查过程中发现新风险，追加写入

### 不适用场景

- 红队杀伤性假设测试 → 使用 hw-red-team
- 项目复盘 → 使用 hw-retro
- 仅需确定性校验（Python 脚本）→ 直接运行 validators/scripts/，不需要本 Skill

## 3. Operating Principles（操作原则）

### Principle 1: 只发现问题，不修改文档

Reviewer 永远不直接编辑被审文档。所有问题以 findings 形式输出，由 PM Agent 或人类 PM 决定如何处理。

- **反面行为**：直接修改文档中的措辞、数字、或章节结构。
- **违反后果**：破坏文档溯源链；PM 无法区分"原始内容"和"Reviewer 修改"；Gate 审批时无法判断问题是否已解决。

### Principle 2: 不确定时默认 refute

在 3-Lens 对抗性验证中，当无法确定一个声明是否可信时，默认标记为 refute（KILL 或 FLAG），而非默认通过。宁可错杀一个真实声明，也不放过一个虚假声明。

- **反面行为**：证据不足时给"通过"，或仅标注"需关注"但降级为 low severity。
- **违反后果**：虚假声明进入产品定义，导致下游决策建立在错误前提上；错误在后续阶段被放大。

### Principle 3: 区分证据问题与意见分歧

Reviewer 标记的是 **可验证的证据问题**（源不支撑声明、数据矛盾、源已过时），而非 **方法论偏好或风格差异**。如果 Reviewer 不同意 PM 的策略选择但无证据支撑，应标记为 `submit_decision` 而非 `must_fix`。

- **反面行为**：将 Reviewer 的主观判断（"这个定位我不认同"）包装成 blocker finding。
- **违反后果**：过度审查导致 PM 失去决策权；Gate 审批被噪音淹没，真正的证据问题被忽视。

### Principle 4: 以 CSV 为权威真相源

当报告中的声明与 CSV 台账记录不一致时，以 CSV 为准。这是系统的确定性规则（AGENTS.md 第 3 条质量底线 + V-06 校验规则）。

- **反面行为**：发现不一致时采信报告内容而忽略 CSV，或在 findings 中不指明不一致。
- **违反后果**：台账数据漂移未被发现；traceability 链路断裂；后续 Gate 校验脚本报 blocker 时难以定位根因。

### Principle 5: 每条 finding 必须可定位

每条 finding 必须包含 `location` 字段，精确到章节号、段落、或 CSV 行号。PM Agent 需要根据 location 定位问题并修正。

- **反面行为**："整体证据质量偏低"这种没有具体位置的模糊发现。
- **违反后果**：PM Agent 无法定位问题，finding 被忽略；问题持续存在到下一阶段。

### Principle 6: Blocker 必须阻碍 Gate

severity=blocker 的 finding 意味着文档不可进入 Gate 审批。Reviewer 有责任将 verdict 设为 `rejected` 当存在任何 blocker。

- **反面行为**：存在 blocker finding 但 verdict 仍为 `approved` 或 `conditional`。
- **违反后果**：Gate 审批建立在有严重缺陷的文档之上；人类 PM 在不知情下批准问题文档。

## 4. Instructions（分步骤指引）

### Step 1: 加载审查对象与关联台账

- **输入**：
  - `review-request` YAML（含 artifact_id, artifact_type, artifact_path, input_artifacts）
  - 待审文档（artifact_path 指向的 .md 文件）
  - 关联 CSV 台账：
    - 所有审查：`registers/evidence.csv`
    - 所有审查：`registers/assumptions.csv`
    - 所有审查：`registers/risks.csv`
    - PRD 审查增加：`registers/requirements.csv`, `registers/traceability.csv`
    - 含决策记录时增加：`registers/decisions.csv`

- **操作**：
  1. 解析 review-request，提取 artifact_id、artifact_type、版本号
  2. 读取待审文档全文
  3. 读取所有关联 CSV 台账
  4. 验证 input_artifacts 声明的上游文档是否存在且版本一致
  5. 确定审查范围：
     - `research_report`：market_study / user_research / competitive_analysis / compliance_research / patent_analysis
     - `product_document`：product_strategy / mrd / brd / product_definition / prd / validation_plan

- **检查点**：
  - [ ] review-request 中所有字段完整
  - [ ] 待审文档文件存在且可读
  - [ ] 至少 evidence.csv 已加载（所有审查类型的必需台账）
  - [ ] artifact_type 是已知类型
  - [ ] 审查范围已确定

### Step 2: 结构完整性检查

- **输入**：已加载的待审文档 + artifact_type

- **操作**：
  1. 根据 artifact_type 确定必需的章节结构：
     - `research_report`：摘要（≤500字）、方法说明、正文分析、输入来源表
     - `product_strategy`：三定（定位/定标/定价）、MVP 定义、路线图
     - `prd`：功能模块、软件模块、硬件模块、结构模块（四模块完整性）
     - `validation_plan`：验证项、方法、判定标准、与假设/风险的关联
  2. 逐章检查：
     - 必需章节是否存在
     - 章节编号是否连续、无跳号
     - 章节标题是否与模板一致
  3. 扫描占位符：搜索 `TBD`、`TODO`、`待补充`、`待定`、`XXX`、`???`
  4. 扫描明显截断：文档末尾是否不自然地中断

- **检查点**：
  - [ ] 所有必需章节存在
  - [ ] 每个缺失章节记录为一条 finding（category=scope, severity=high）
  - [ ] 每个占位符记录为一条 finding（category=scope, severity=medium）
  - [ ] 每条 finding 的 location 指向具体章节号

### Step 3: 证据质量检查

- **输入**：待审文档内容 + evidence.csv 全部记录

- **操作**：
  1. 提取文档中所有引用的 evidence_id（搜索 `EV-` 前缀模式）
  2. 对每个引用的 evidence_id：
     - 验证 evidence.csv 中存在对应记录（不存在 → finding, severity=blocker, category=evidence）
     - 验证 `source_grade` 字段非空（为空 → finding, severity=medium, category=evidence）
     - 验证 `source_grade` 值为有效枚举 A/B/C/D（无效 → finding, severity=medium, category=evidence）
  3. 对 importance=central 的 evidence 记录：
     - 验证 `direct_quote` 字段非空（为空或仅含"示例数据" → finding, severity=high, category=evidence）
     - 检查 direct_quote 是否为 Agent 改写而非源文直接引述：
       - 特征 1：没有引号包裹的具体语句
       - 特征 2：读起来像概括而非原文（如"市场规模很大且在增长"）
       - 特征 3：引述内容不包含具体数字但声明包含数字
       - 上述任一特征匹配 → finding, severity=high, category=evidence
  4. 检查重要性虚高：所有 evidence 都标记为 central → finding, severity=medium, category=evidence
  5. 检查外推过度：声明范围明显超出 direct_quote 所支撑的范围 → finding, severity=high, category=evidence

- **检查点**：
  - [ ] 文档中引用的所有 evidence_id 在 evidence.csv 中存在
  - [ ] 所有 central evidence 有非空的 direct_quote
  - [ ] 识别出的 Agent 改写模式已记录为 finding
  - [ ] 识别的外推过度已记录为 finding

### Step 4: 3-Lens 对抗性验证（C 级源高风险声明）

- **输入**：Step 3 中识别出的 C 级源声明（source_grade=C）+ importance=central 或涉及高风险断言（如市场规模数字、竞品关键参数、合规要求）

- **操作**：
  1. **筛选待验证声明**：从所有 C 级源声明中选出 importance=central 或涉及高风险断言的声明。总数上限 25 条。优先选择：
     - 支撑核心结论的声明
     - 包含具体数字的声明
     - 涉及产品关键决策（定位/定价/认证路径）的声明
  2. 对每条声明，执行三镜头核验：

     **Lens 1: 源忠实度（Source Fidelity）**
     - 重读源文（如 URL 可访问则 WebFetch 获取原文）
     - 核对 direct_quote 中的数字是否确实来自源文
     - 检查是否断章取义（quote 的上下文是否改变了含义）
     - 搜索源文是否有其他解读角度
     - 判定 refute 条件：源没有声明这个数字；声明超出源支撑范围；引述被断章取义

     **Lens 2: 矛盾搜索（Contradiction Hunt）**
     - 对声明中的关键数字/断言，搜索对立面（如"市场规模并非 X 亿"、"实际数据远低于"、"XX 报告显示不同"）
     - 对找到的矛盾源，评估其可信度（source_grade 是否 ≥ 被审查的源）
     - 判断矛盾类型：直接反驳（同一指标不同数字）vs 方法论差异（统计口径不同）
     - 判定 refute 条件：更高可信度源直接矛盾；多个独立源报告显著不同数字（偏差 >30%）；官方数据与声明冲突

     **Lens 3: 时效与偏见（Freshness & Bias）**
     - 核对源的发布时间（超过 2 年 → 标记）
     - 识别源的利益冲突：品牌自述/赞助报告/电商平台（销售导向）/供应商报价（营销导向）
     - 搜索是否存在更近期的数据
     - 判定 refute 条件：数据明显过时（>3 年且领域变化快）；未披露的利益冲突；内容读起来像营销文案而非事实报告

  3. **投票判定**：
     - ≥2 个 lens refute → **KILL**：该声明排除出核心结论，移至 Refuted 附录
     - 1 个 lens refute → **FLAG**：声明可使用，但必须附加可见的不确定性说明
     - 0 个 lens refute → **PASS**：声明经对抗性审查存活，标注"3-Lens Verified"
     - 不确定时默认 refute：当证据不足以做出明确判定的，按 refute 处理

  4. **记录验证结果**：
     - KILLED 声明 → finding (severity=blocker, category=evidence, required_action=must_fix)，要求在文档中移除此声明或将声明移至 Refuted 附录
     - FLAGGED 声明 → finding (severity=high, category=evidence, required_action=must_fix)，要求附加不确定性说明
     - PASSED 声明 → 不生成 finding，但在审查摘要中记录验证通过数

- **检查点**：
  - [ ] 待验证声明总数 ≤ 25
  - [ ] 每条待验证声明完成了三镜头检查
  - [ ] 所有 KILLED 声明已记录 refute 原因和 lens
  - [ ] 所有 FLAGGED 声明已记录不确定因素
  - [ ] 验证结果汇总（PASS/FLAG/KILL 计数）

### Step 5: 一致性交叉校验（报告 vs CSV）

- **输入**：待审文档 + 所有已加载的 CSV 台账

- **操作**：
  1. 执行确定性校验规则（architecture.md 七.2）：

     | 规则 | 检查内容 | 严重级别 |
     |------|---------|---------|
     | V-01 | 每条 P0/P1 requirement 有 ≥1 条 traceability 记录 | blocker |
     | V-02 | traceability 中引用的 evidence_id 在 evidence.csv 中存在 | blocker |
     | V-03 | traceability 中引用的 requirement_id 在 requirements.csv 中存在 | blocker |
     | V-04 | assumptions 中 confidence=高 但没有 validation_method | high |
     | V-05 | risks 中 impact=高 但没有 mitigation | blocker |
     | V-06 | evidence 的 source_grade 不为空 | medium |
     | V-07 | ID 格式符合 `{type}-{project}-{seq}` 规范，无跨文件重复 | blocker |
     | V-08 | 已批准 artifact 有关联 decision_id | blocker |

  2. 报告声明与 CSV 记录交叉比对：
     - 文档中提到"据 evidence.csv 记录..."但 CSV 中无此记录 → finding, severity=high, category=consistency
     - 文档中的数字与 CSV 中对应 evidence 的 direct_quote 不一致 → finding, severity=blocker, category=consistency
     - 文档声称"X 个 evidence 支撑"但实际可追溯的 evidence 数量不足 → finding, severity=medium, category=consistency

  3. 输入来源表验证（仅研究报告）：
     - 检查"输入来源表"章节是否存在
     - 逐行核对每个输入项的状态是否为"已获取/缺失/不适用"之一
     - 状态为"缺失"但未说明原因 → finding, severity=high, category=consistency

- **检查点**：
  - [ ] V-01 ~ V-08 全部执行
  - [ ] 每条规则违反记录为独立 finding（category=consistency）
  - [ ] CSV 与报告不一致处已记录，以 CSV 为准
  - [ ] 输入来源表中的缺失项已识别

### Step 6: 输出审查结果

- **输入**：Step 2~5 的全部 findings

- **操作**：
  1. 汇总所有 findings，按 severity 排序（blocker > high > medium > low）
  2. 为每条 finding 分配 finding_id（格式 `F-{project}-{seq}`）
  3. 判定 verdict：
     - 存在任何 blocker → `rejected`
     - 无 blocker 但有 high/medium → `conditional`（附带条件通过）
     - 无 blocker 且无 high，仅 low/medium → `approved`
     - 无任何 finding → `approved`
  4. 编译 review-result YAML（完整格式见 Output Structure）
  5. 写入审查摘要（审查范围、验证声明数、PASS/FLAG/KILL 计数、关键发现）
  6. 如果在审查过程中发现了 evidence.csv 或 risks.csv 中未记录的新风险 → 追加写入 `registers/risks.csv`：
     - risk_id: `RISK-{project}-{seq}`
     - risk: 风险描述
     - category: 对应类别
     - probability: 基于发现的评估
     - impact: 基于发现的评估
     - trigger: 触发条件
     - related_evidence: 关联的 evidence_id

- **检查点**：
  - [ ] 每条 finding 包含全部必需字段（finding_id, severity, category, location, finding, required_action）
  - [ ] verdict 与 finding 严重级别一致（有 blocker → rejected）
  - [ ] finding_id 无重复
  - [ ] 审查摘要包含 PASS/FLAG/KILL 计数
  - [ ] 新风险已写入 risks.csv（如适用）

## 5. Output Structure（输出结构）

### 输出文件

1. **审查结果**（返回给 PM Agent，不落盘为独立文件）：review-result YAML
2. **风险台账更新**：`registers/risks.csv`（如发现新风险）

### review-result YAML 完整模板

```yaml
review-result:
  review_id: "REV-{project}-{seq}"
  artifact_id: "ART-{project}-{seq}"
  artifact_type: "market_study | user_research | competitive_analysis | compliance_research | patent_analysis | product_strategy | mrd | brd | product_definition | prd | validation_plan"
  artifact_version: "v0.1"
  verdict: "approved | conditional | rejected"
  review_date: "YYYY-MM-DD"
  review_scope:
    artifact_type: "{artifact_type}"
    input_artifacts:
      - artifact_id: "ART-{project}-{seq}"
        version: "v1.0"
    registers_checked:
      - "registers/evidence.csv"
      - "registers/assumptions.csv"
      - "registers/risks.csv"
      - "registers/requirements.csv"       # PRD 审查时
      - "registers/traceability.csv"       # PRD 审查时
      - "registers/decisions.csv"          # 含决策记录时
  verification_summary:
    claims_verified: 0           # 3-Lens 验证的声明总数
    claims_passed: 0             # PASS 数
    claims_flagged: 0            # FLAG 数
    claims_killed: 0             # KILL 数
    verification_budget_used: 0  # 实际使用的验证配额（max 25）
  findings:
    - finding_id: "F-{project}-{seq}"
      severity: "blocker | high | medium | low"
      category: "evidence | scope | requirement | acceptance | validation | risk | consistency"
      location: "第X章 第Y节 / 段落 / evidence_id: EV-xxx-xxx / CSV行号"
      finding: "具体问题描述，包含问题是什么、为什么是问题、如何验证的"
      source_lens: "lens_1 | lens_2 | lens_3 | null"   # 仅 evidence category 的 3-Lens 验证结果填写
      required_action: "must_fix | suggest | submit_decision"
  new_risks_written:
    - risk_id: "RISK-{project}-{seq}"   # 仅当 Step 6 写入新风险时
```

### severity 判定标准

| severity | 条件 | 对 verdict 的影响 |
|----------|------|------------------|
| **blocker** | 文档存在致命缺陷：证据不存在、P0 需求无追踪、CSV 数据矛盾、声明被 KILL | verdict = rejected |
| **high** | 文档存在重要缺陷但可修正：central claim 缺 direct_quote、高置信假设无验证方法、C 级声明被 FLAG | 无 blocker 时 verdict = conditional |
| **medium** | 文档存在质量问题但不影响决策：source_grade 缺失、重要性虚高、低影响的 CSV 不一致 | 不影响 verdict 判定 |
| **low** | 优化建议：措辞改进、补充说明、格式规范 | 不影响 verdict 判定 |

### category 分类标准

| category | 适用场景 |
|----------|---------|
| **evidence** | 证据不存在、源不支撑声明、direct_quote 缺失、source_grade 无效、3-Lens 验证结果 |
| **scope** | 章节缺失、占位符、内容截断、四模块不完整 |
| **requirement** | 需求未追踪、P0/P1 无 traceability、需求不可验证 |
| **acceptance** | 验收标准缺失或不可量化 |
| **validation** | 验证计划项缺失、验证方法与风险不对应 |
| **risk** | 风险未登记、高影响风险无缓解措施 |
| **consistency** | 报告与 CSV 不一致、输入来源表缺失项、跨文档矛盾 |

### required_action 判定标准

| required_action | 含义 | 适用场景 |
|-----------------|------|---------|
| **must_fix** | 必须修正后才能进入 Gate | blocker + high severity findings |
| **suggest** | 建议修正，PM 自行决定 | medium + low severity findings |
| **submit_decision** | Reviewer 无法判断，提交 PM 决策 | Reviewer 发现潜在问题但无证据支撑，或涉及策略选择 |

### risks.csv 追加格式

当 Step 6 发现新风险时，追加一行到 `registers/risks.csv`：

```csv
RISK-{project}-{seq},{风险描述},{市场/用户/技术/供应链/认证/质量/售后/商业},{高/中/低},{高/中/低},{触发条件},{缓解建议},{owner},{待处理},{关联evidence_id},
```

## 6. Quality Bar（最低质量标准）

审查完成后，Reviewer 自身输出必须满足以下条件：

- [ ] **Finding 完整性**：每条 finding 包含全部 6 个必需字段（finding_id, severity, category, location, finding, required_action）。缺少任一字段的 finding 不输出。

- [ ] **Verdict 一致性**：verdict 与 finding 严重级别数学一致 —— 存在 blocker → rejected；存在 high 且无 blocker → conditional；仅 medium/low → approved。不一致的 verdict 视为 Reviewer 自身错误。

- [ ] **3-Lens 覆盖率**：所有 C 级源 + importance=central 的声明中，至少选择最重要的 min(25, 实际数量) 条进行对抗性验证。验证声明数 < 实际应验证数的 50% 视为审查不充分。

- [ ] **KILLED 声明可追溯**：每条 KILLED 声明记录了 (a) 哪个 lens 触发了 refute, (b) refute 的具体原因, (c) 矛盾源的可信度对比。缺少任一要素的 KILL finding 视为无效。

- [ ] **CSV 权威性保持**：所有 consistency finding 以 CSV 为准。当报告与 CSV 不一致时，finding 中指出的"正确值"来自 CSV 而非报告。

- [ ] **审查摘要完整**：包含 (a) 审查范围, (b) 验证声明总数及 PASS/FLAG/KILL 计数, (c) blocker 清单, (d) 审查结论。

- [ ] **无 Reviewer 自身的主观判断混入**：所有 blocker 和 high finding 可追溯到具体证据（源文内容、CSV 记录、模板规范）。无法追溯的 blocker 不成立。

## 7. Tool Integration（工具链）

### 主工具及边界

| 工具 | 用途 | 边界 |
|------|------|------|
| **Read** | 读取待审文档、CSV 台账、上游文档 | 不修改任何文件 |
| **WebFetch** | 3-Lens Lens 1 重读源文；Lens 2 搜索矛盾源；Lens 3 搜索更近期数据 | 仅获取公开可访问 URL；不访问需认证的页面 |
| **WebSearch** | Lens 2 矛盾搜索：搜索对立关键词；Lens 3 搜索更近期数据 | 每次搜索 ≤ 3 个 query |
| **Bash** | grep 搜索文档中的 evidence_id 引用、TBD 占位符、ID 格式校验 | 仅读操作；不执行写操作 |
| **Write/Edit** | 写入 risks.csv（仅在 Step 6 发现新风险时） | 仅追加，不修改已有记录；不修改被审文档 |

### 降级链

| 主工具场景 | 不可用时 | 降级方案 |
|-----------|---------|---------|
| WebFetch 获取源文 | 源 URL 不可访问（404/认证墙/超时） | Lens 1 标记为"源不可访问，无法核验忠实度"→ 按 refute 处理（不确定时默认 refute） |
| WebSearch 矛盾搜索 | 搜索工具不可用或返回空结果 | Lens 2 标记为"无法执行矛盾搜索"→ 不影响投票（该 lens 不产生 refute），但记录在 finding 中 |
| WebSearch 时效检查 | 搜索工具不可用 | Lens 3 仅基于已有的源日期字段判断 → 无法确认时效性时标记"时效性未验证" |
| Bash 校验 ID 格式 | 跨文件重复检查需要 grep 多个 CSV | 手动逐文件检查 ID 唯一性 |

### 质量门禁阈值

| 检查项 | 阈值 | 不满足时的处理 |
|--------|------|--------------|
| 待验证声明筛选 | ≤ 25 条 | 超过 25 条时，按风险排序取前 25 条；其余标记为"验证配额不足，未验证" |
| 矛盾搜索结果置信度 | 矛盾源 source_grade ≥ 被审源才触发 refute | 低可信度矛盾源仅记录，不触发 KILL/FLAG |
| Lens 1 源文获取成功率 | — | 无法获取源文时仍记录，按 refute 处理 |

## 8. Best Practices（最佳实践）

### 好的 Finding vs 差的 Finding

**好的 Finding（可操作、可定位、可验证）**：

```yaml
- finding_id: "F-CWLS-001"
  severity: "blocker"
  category: "evidence"
  location: "第3.2章 市场规模 / evidence_id: EV-CWLS-003"
  finding: "声明'中国智能门锁市场规模约120亿元'的 direct_quote 为'市场规模可观，智能锁渗透率持续提升'。引述内容不包含具体数字120亿，但声明包含精确数字。这是 Agent 过度外推——源说方向，声明给数字。3-Lens Lens 1 核验：源文通篇无120亿数字。"
  source_lens: "lens_1"
  required_action: "must_fix"
```

**差的 Finding（模糊、不可操作）**：

```yaml
- finding_id: "F-CWLS-002"
  severity: "high"
  category: "evidence"
  location: "全文"
  finding: "证据质量普遍偏低，建议提升。"
  required_action: "suggest"
```
问题：location 是"全文"，PM 不知道该改哪里；finding 没有说明什么证据、为什么低、如何提升；没有可验证的判断标准。

### 常见陷阱

1. **把 Reviewer 的策略偏好包装成 blocker**：如果 PM 选择定位 A 而非 B，而 A/B 都有合理证据支撑，这不构成 finding。标记为 `submit_decision` 并说明"定位 B 有 X 证据支撑，但定位 A 也有 Y 支撑 —— 请 PM 决策"。

2. **3-Lens 验证时过度依赖单一搜索词**：Lens 2 矛盾搜索需要尝试多个对立关键词。仅搜索"市场规模 120亿" → 只会找到重复该数字的源。需要搜"市场规模 80亿"、"市场实际规模"、"XX 报告质疑"等。

3. **忽略"没有 finding"的审查结果**：如果审查确实没有发现问题，verdict 应为 approved，而不是强行找几个 low severity finding 来"证明做了审查"。无 finding 的 approved 是合法的审查结果。

4. **跨文档审查时混淆 artifact**：当 PRD 引用市场研究报告中的 evidence 时，Reviewer 需要检查 (a) evidence 在当时的报告中是否正确, 和 (b) PRD 引用时是否正确理解。不要因为市场研究报告有旧 finding 而重复标记。

5. **忘记 CSV 是权威**：发现报告说"3 个 evidence 支撑需求 X"，但 traceability.csv 只有 2 条记录。应标记报告描述不准确（consistency finding），而不是修改 CSV 来凑够 3 条。

### 审查策略优先级

资源有限时，按以下优先级分配审查精力：

1. **Blocker 级别问题**（最高优先级）：证据不存在、声明被 KILL、P0 需求无追踪
2. **高影响证据问题**：central claim 缺 direct_quote、C 级源支撑核心结论
3. **一致性交叉校验**：V-01 ~ V-08 确定性规则
4. **结构完整性**：章节缺失、占位符
5. **优化建议**：措辞改进、格式规范

## 9. Further Reading（扩展阅读）

### 关联模板

- 研究报告模板：`templates/` 目录下各研究报告模板（含摘要 ≤500字 + 输入来源表章节规范）
- 产品文档模板：`templates/` 目录下 PRD、产品定义、验证计划等模板

### 关联台账

- `registers/evidence.csv` — 证据台账（source_grade 字段定义对应 architecture.md 十三.2.1）
- `registers/assumptions.csv` — 假设台账（confidence + validation_method 字段）
- `registers/risks.csv` — 风险台账（本 Skill 审查时发现新风险则追加写入）
- `registers/requirements.csv` — 需求台账（P0/P1 requirement 必须被 traceability 关联）
- `registers/traceability.csv` — 追踪台账（中心 JOIN 表，执行 V-01~V-03 校验）
- `registers/decisions.csv` — 决策台账（V-08 校验对象）

### 方法论参考

- `docs/architecture.md` 第十三章 — pm-skills 方法论参考：
  - 十三.2.1：证据分级体系 A/B/C/D（source_grade 定义）
  - 十三.2.2：Falsifiable Claim 提取规则（5 条规则 + 4 种失败模式）
  - 十三.2.3：3-Lens 对抗性验证（本 Skill Step 4 的完整方法论）
  - 十三.2.5：阶段审计模板（Gate 前置检查）
- `docs/architecture.md` 第五章 — Agent 通信协议：
  - 五.2：PM → Reviewer 的契约（review-request 格式）
  - 五.3：Reviewer → PM 的契约（review-result 格式，本 Skill 的输出格式定义）
- `docs/architecture.md` 第七章 — 台账机制：
  - 七.1：台账写入规则（Reviewer 写入 risks.csv 的时机）
  - 七.2：确定性校验规则 8 条（V-01 ~ V-08，本 Skill Step 5 的执行依据）

### 参考 Skills

- `market-deep-research`（pm-skills）— 3-Lens 对抗性验证方法论来源；证据分级标准来源
- `hw-red-team` — Reviewer 的第二个 Skill，红队杀伤性假设测试。输入为 PRD + 产品定义 + 假设，输出为杀伤性假设 + 验证方案。与本 Skill 互补：本 Skill 审查文档质量，hw-red-team 挑战产品假设
- `hw-gate-prep` — 消费本 Skill 的 review-result，汇总 findings 生成 Gate 摘要

### 系统上下文

- `AGENTS.md` — 3-Agent 协作系统定义：
  - 第 1 节：Reviewer 角色定义（"做得对吗？"）
  - 第 3 节：6 条质量底线（CSV 是权威、摘要 ≤500 字、四模块完整性等）
  - 第 5 节：台账规则（ID 格式、写入时机、关联规则）
  - 第 6 节：人工门径规则（Gate 位置、条件、检查流程）
- `skills/SKILL_TEMPLATE.md` — Skill 编写范式（本文件遵循的 9 章节模板）
