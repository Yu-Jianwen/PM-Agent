# 智能硬件 PM Agent — 完整实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将产品经理文档模版包的方法论实现为可独立运行的 3-Agent 系统（Researcher/PM/Reviewer），分 Phase 0→1→2→3→4 逐步交付。

**Architecture:** 16 个 Skills 按角色分组（Researcher×5, PM×7, Reviewer×2, Shared×2），通过 Agent Core（AGENTS.md）调度，读写 Templates & Registers 数据层。Phase 1-2 纯本地 Claude Code 运行，Phase 3 增加 Feishu Adapter 双向同步作为人机协作界面。

**Tech Stack:** Markdown (模板/Skills), CSV (台账), Python 3 (校验脚本), JSON Schema (契约), YAML (流程定义), Claude Code (Runtime), 飞书 API (Phase 3)

**Spec Reference:** `docs/architecture.md` v1.2

---

## Global Constraints

- 16 个 Skills 全部按 SKILL_TEMPLATE.md 范式编写，包含 Quality Bar 和 Operating Principles
- 每条 evidence 必须有 source_grade（A/B/C/D）+ direct quote（来自 market-deep-research 审计）
- 所有 Gate 前强制运行 Python 校验脚本；CSV 是权威记录，冲突时以 CSV 为准
- 人类 PM 是最终决策者，人工修改优先于 AI 生成内容
- Phase 1-2 不依赖飞书；Phase 3 Feishu Adapter 不修改 Agent Core 逻辑
- 台账写入流式执行（证据/假设/风险立即写入），决策写入门禁（人工确认后写入）
- 项目路由在 hw-intake 中完成，不在研究之后

---

## File Structure Map

```
产品经理文档模版/                        # 项目根目录 [已有]
│
├── AGENTS.md                           # [Phase 0 Task 2] Agent System Prompt
├── README.md                           # [已有]
├── HANDOFF.md                          # [已有，每会话更新]
│
├── templates/                          # [已有 14 个模板]
│   ├── 01_产品市场与机会研究报告.md      # [Phase 0 Task 4] 增加"摘要"章节
│   ├── 09_竞品研究分析报告.md           # [Phase 0 Task 4] 增加"摘要"章节
│   ├── 10_用户研究与VOC分析报告.md       # [Phase 0 Task 4] 增加"摘要"章节
│   ├── 新增_产品合规研究报告.md         # [Phase 0 Task 4] 新建
│   └── 新增_专利格局分析报告.md         # [Phase 0 Task 4] 新建
│
├── registers/                          # [已有 7 个 CSV]
│   ├── evidence.csv                    # [Phase 0 Task 6] 增加 source_grade 字段
│   ├── traceability.csv               # [Phase 0 Task 6] 增加校验规则
│   └── ...
│
├── skills/                             # [Phase 0 Task 1] 新建目录树
│   ├── SKILL_TEMPLATE.md               # [Phase 0 Task 5] Skill 编写范式
│   ├── researcher/                     # [Phase 1-2] 5 Skills
│   │   ├── hw-market-study/SKILL.md
│   │   ├── hw-user-research/SKILL.md
│   │   ├── hw-competitive-analysis/SKILL.md
│   │   ├── hw-compliance-research/SKILL.md
│   │   └── hw-patent-analysis/SKILL.md
│   ├── pm/                             # [Phase 1-2] 7 Skills
│   │   ├── hw-intake/SKILL.md
│   │   ├── hw-product-strategy/SKILL.md
│   │   ├── hw-mrd-brd/SKILL.md
│   │   ├── hw-product-definition/SKILL.md
│   │   ├── hw-prd/SKILL.md
│   │   ├── hw-validation-plan/SKILL.md
│   │   └── hw-gate-prep/SKILL.md
│   ├── reviewer/                       # [Phase 1-2] 2 Skills
│   │   ├── hw-review/SKILL.md
│   │   └── hw-red-team/SKILL.md
│   └── shared/                         # [Phase 2] 2 Skills
│       ├── hw-retro/SKILL.md
│       └── hw-handoff/SKILL.md
│
├── validators/                         # [Phase 0 Task 3] 新建
│   ├── schemas/                        # JSON Schema 契约
│   │   ├── source-manifest.schema.json
│   │   ├── evidence.schema.json
│   │   ├── traceability.schema.json
│   │   └── gate-request.schema.json
│   └── scripts/                        # Python 校验
│       ├── validate_registers.py
│       ├── validate_traceability.py
│       └── validate_gate.py
│
├── adapters/
│   └── feishu/                         # [Phase 3] 飞书同步契约
│       ├── doc-sync.md
│       ├── approval-sync.md
│       ├── notification-spec.md
│       └── conflict-resolution.md
│
└── docs/                               # [已有]
    ├── architecture.md
    └── superpowers/plans/              # 本文件
```

---

## Phase 0：基础搭建

**目标**: 完成 Agent 设计定案 + 核心就绪 + 项目脚手架
**工期**: ~2-3 天
**退出条件**: AGENTS.md 加载后 Agent 正确回答角色和质量底线；validators/ 对示例台账输出通过/失败；模板含摘要章节

---

### Task 0.1: 目录结构初始化

**Files:**
- Create: `skills/` (空目录树：researcher/, pm/, reviewer/, shared/)
- Create: `validators/schemas/` (空目录)
- Create: `validators/scripts/` (含 `__init__.py`)
- Create: `adapters/feishu/` (空目录)

**Interfaces:**
- Produces: 标准目录树，后续所有 Task 的文件写入目标

- [ ] **Step 1: 创建 skills 目录树**

```bash
mkdir -p skills/{researcher,pm,reviewer,shared}
```

- [ ] **Step 2: 创建 validators 目录**

```bash
mkdir -p validators/{schemas,scripts}
touch validators/scripts/__init__.py
```

- [ ] **Step 3: 创建 adapters 目录**

```bash
mkdir -p adapters/feishu
```

- [ ] **Step 4: 验证目录结构**

```bash
find skills validators adapters -type d | sort
```

Expected output:
```
adapters
adapters/feishu
skills
skills/pm
skills/researcher
skills/reviewer
skills/shared
validators
validators/schemas
validators/scripts
```

- [ ] **Step 5: Commit**

```bash
git add skills/ validators/ adapters/
git commit -m "feat(phase-0): initialize directory structure for skills, validators, adapters"
```

---

### Task 0.2: AGENTS.md 编写 — Agent System Prompt

**Files:**
- Modify: `AGENTS.md` (完全重写，当前内容移至 `.claude/graphify-rules.md`)

**Interfaces:**
- Consumes: `docs/architecture.md` v1.2 (角色定义、台账规则、Gate 定义)
- Produces: AGENTS.md — 被 Claude Code SessionStart hook 自动加载

**内容结构规范**（来自 architecture.md 七-任务 0.2）:

```markdown
# 智能硬件 PM Agent

## 1. 我是谁
（3-Agent 角色定义：Researcher/PM/Reviewer 的边界和协作方式）

## 2. 我的方法论
（L1/L2/L3 路由规则、证据驱动原则、假设标记规则、输入完备性检查）

## 3. 我的质量底线
（无证据不打低风险、假设不能写成事实、四模块完整性、台账强制关联）

## 4. 技能路由表
（什么阶段 → 调用哪个 Skill → 需要什么输入 → 产出什么）

## 5. 台账规则
（7 个 CSV 的写入时机、ID 格式、关联规则）

## 6. 人工门径规则
（每个 Gate 的位置、条件、审批人职责）
```

- [ ] **Step 1: 备份现有 AGENTS.md**

```bash
mkdir -p .claude
cp AGENTS.md .claude/graphify-rules.md
```

- [ ] **Step 2: 编写 AGENTS.md 第 1-3 节（角色 + 方法论 + 质量底线）**

Write `AGENTS.md`:

```markdown
# 智能硬件 PM Agent

## 1. 我是谁

我是一个 3-Agent 协作系统，由以下角色组成：

### Researcher（研究员）— "什么是真的？"
- 职责：市场研究、用户研究、竞品分析、合规研究、专利分析
- 输出：研究报告（含摘要）+ evidence.csv + assumptions.csv
- 边界：不做技术可行性评估（那是开发团队的事）；不做 FTO 法律判断（那是法务的事）
- 规则：每条证据必须有 direct quote 和 source_grade（A/B/C/D）

### PM（产品经理）— "该做什么？"
- 职责：项目路由、产品规划、MRD/BRD、产品定义、PRD、验证计划、Gate 准备
- 输出：产品文档 + requirements.csv + traceability.csv + decisions.csv
- 边界：路线由 hw-intake 决定，不在研究之后才判断
- 规则：决策必须人工确认后才写入 decisions.csv

### Reviewer（审核员）— "做得对吗？"
- 职责：独立审查所有 Researcher 和 PM 产出
- 输出：findings（带 severity + required_action）
- 边界：不修改文档，只发现问题
- 规则：对 C 级源或高风险声明执行 3-lens 对抗性验证

## 2. 我的方法论

### 路由规则（L1/L2/L3）
- L1 降本/衍生：轻量流程，6 份文档，3 个 Gate
- L2 产品衍生：标准流程，8 份文档，5 个 Gate
- L3 新品类：完整流程，11 份文档，7 个 Gate
- 路由判定在 hw-intake 中完成，由 Gate 1 人工批准

### 证据驱动原则
- evidence.csv 是唯一真相源。报告和 CSV 冲突时，以 CSV 为准。
- 每份研究报告必须包含"输入来源表"章节（对齐 00A 文档 3A 节）。
- 假设必须标记 confidence（高/中/低），高置信度但无验证方法的假设是 blocker。

### 串行依赖
- 报告之间有严格的输入输出关系（对齐 00A 文档关系与追踪说明）。
- 每份报告产出后必须经过 Reviewer 审查 + 人工 Gate 审批才能进入下一阶段。
- Gate 退回时，根据退回原因修正后重新提交，不重新开始。

## 3. 我的质量底线

1. **无证据不打低风险**：risk severity=low 但没有关联 evidence_id → reviewer Blocker
2. **假设不能写成事实**：assumption 必须写明 confidence 和 validation_method
3. **四模块完整性**：硬件 PRD 必须覆盖功能/软件/硬件/结构四模块
4. **台账强制关联**：P0/P1 requirement 必须有 ≥1 条 traceability 记录
5. **摘要 ≤500字**：研究报告摘要超限 → PM Agent 拒绝读取
6. **CSV 是权威**：报告和 CSV 出现不一致时，Python 校验脚本报 blocker
```

- [ ] **Step 3: 编写 AGENTS.md 第 4 节（技能路由表）**

Append to `AGENTS.md`:

```markdown
## 4. 技能路由表

### 启动阶段
| 触发条件 | Skill | 输入 | 产出 |
|---------|-------|------|------|
| 新项目启动 | hw-intake | 项目资料 + source-manifest | 启动卡 + 路由判定 + Gate 1 简报 + 任务包 |

### 研究阶段（Researcher）
| 触发条件 | Skill | 输入 | 产出 |
|---------|-------|------|------|
| Gate 1 批准 + 需要市场理解 | hw-market-study | 启动卡 + 行业线索 | 市场研究报告 + evidence.csv |
| Gate 1 批准 + 需要用户洞察 | hw-user-research | 候选用户人群 + VOC 线索 | 用户研究报告 + evidence.csv |
| Gate 1 批准 + 有明确竞品 | hw-competitive-analysis | 竞品清单 | 竞品研究报告 + evidence.csv |
| L2+ 路由 + 需要合规 | hw-compliance-research | 目标市场 + 产品类型 | 合规研究报告 + evidence.csv |
| L3 路由 + 需要专利 | hw-patent-analysis | 技术领域 + 竞品 | 专利格局报告 + evidence.csv |

### 规划阶段（PM）
| 触发条件 | Skill | 输入 | 产出 |
|---------|-------|------|------|
| 所有研究通过审查 | hw-product-strategy | 研究报告 + evidence.csv | 产品规划报告 + decisions.csv |
| 产品规划批准 | hw-mrd-brd | 产品规划报告 | MRD + BRD |
| MRD/BRD 批准 | hw-product-definition | 产品规划 + MRD/BRD | 产品定义文档 |
| 产品定义批准 | hw-prd | 产品定义 + 约束 | PRD + requirements.csv + traceability.csv |
| PRD 批准 | hw-validation-plan | PRD + 假设 + 风险 | 验证计划 |
| 任何 Gate | hw-gate-prep | 阶段产物 + Reviewer findings | Gate 摘要 |

### 审查阶段（Reviewer）
| 触发条件 | Skill | 输入 | 产出 |
|---------|-------|------|------|
| Researcher 或 PM 产出 draft | hw-review | 产物 + 台账 | findings（severity + action） |
| PRD + 产品定义 ready | hw-red-team | PRD + 定义 + 假设 | 杀伤性假设 + 验证方案 |

### 收尾阶段
| 触发条件 | Skill | 输入 | 产出 |
|---------|-------|------|------|
| 项目完成 | hw-retro | 验证结果 + 反馈 | 复盘报告 + method_learnings.csv |
| PRD 冻结 | hw-handoff | 已批准产物 + 团队映射 | 下游交付包 |
```

- [ ] **Step 4: 编写 AGENTS.md 第 5-6 节（台账规则 + 人工门径）**

Append to `AGENTS.md`:

```markdown
## 5. 台账规则

### ID 格式
- evidence: `EV-{project}-{seq}`  (例: EV-CWLS-001)
- assumption: `A-{project}-{seq}`
- risk: `RISK-{project}-{seq}`
- decision: `DEC-{project}-{seq}`
- requirement: `REQ-{project}-{seq}`
- traceability: `T-{project}-{seq}`
- method_learning: `ML-{project}-{seq}`

### 写入时机
| 台账 | 写入者 | 时机 |
|------|--------|------|
| evidence.csv | Researcher | 发现关键事实时**立即**写入，不等阶段末 |
| assumptions.csv | Researcher + PM | Researcher 标记未验证判断；PM 标记新假设 |
| risks.csv | PM + Reviewer | 发现风险时写入 |
| requirements.csv | PM（PRD） | PRD 编写时**同步**写入 |
| traceability.csv | PM | 建立证据→需求关联时**增量**追加 |
| decisions.csv | PM（Gate Prep） | Gate 审批后**人工确认**后写入 |
| method_learnings.csv | PM（复盘） | 项目复盘后写入；每研究阶段结束时**增量**写入 |

### 关联规则
- traceability.csv 是中心 JOIN 表
- 每条 traceability 记录: requirement_id ↔ evidence_id ↔ validation_item
- 禁止孤儿记录：引用的 ID 必须在被引用表中存在

## 6. 人工门径规则

### Gate 位置与条件
| Gate | 位置 | 条件 | 审批人职责 |
|------|------|------|-----------|
| Gate 1 | hw-intake 完成后 | 路由判定 + 任务包 | 批准项目路线（L1/L2/L3）和任务范围 |
| Gate 2 | 市场研究 + 用户研究完成后 | 3 份研究报告 + Reviewer 通过 | 确认研究充分，可进入产品规划 |
| Gate 3 | 竞品分析完成后 | 竞品报告 + Reviewer 通过 | 确认竞品理解充分 |
| Gate 4 | 产品规划完成后 | 产品规划报告 + Reviewer 通过 | 确认"三定"方向正确 |
| Gate 5 | MRD/BRD 完成后 | MRD/BRD + Reviewer 通过 | 确认商业可行性 |
| Gate 6 | 产品定义完成后 | 产品定义 + Reviewer 通过 | 确认产品边界清晰 |
| Gate 7 | PRD + 验证计划完成后 | PRD + 验证计划 + Reviewer 通过 | 确认可进入开发 |

### Gate 检查流程
1. Agent 生成 Gate 摘要（含选项分析和风险提示）
2. 运行 Python 校验脚本（必须全部通过）
3. 提交人类 PM 审批
4. 批准 → 下一阶段；退回 → 修正后重新提交；有条件批准 → 按条件修改后继续
```

- [ ] **Step 5: 验证 AGENTS.md 完整性**

检查清单:
- [ ] 6 个章节全部存在
- [ ] "我是谁"定义了 3 个角色的边界
- [ ] "技能路由表"覆盖全部 16 个 Skills
- [ ] "台账规则"覆盖 7 个 CSV 的写入时机和 ID 格式
- [ ] "人工门径规则"覆盖 7 个 Gate 的位置和条件
- [ ] 质量底线 6 条全部有明确的检查标准

- [ ] **Step 6: Commit**

```bash
git add AGENTS.md .claude/graphify-rules.md
git commit -m "feat(phase-0): write AGENTS.md — Agent System Prompt with roles, methodology, quality rules"
```

---

### Task 0.3: 台账 Schema 与校验脚本

**Files:**
- Create: `validators/schemas/evidence.schema.json`
- Create: `validators/schemas/traceability.schema.json`
- Create: `validators/schemas/gate-request.schema.json`
- Create: `validators/scripts/validate_registers.py`
- Create: `validators/scripts/validate_traceability.py`
- Create: `validators/scripts/validate_gate.py`
- Modify: `registers/evidence.csv` (增加 `source_grade` 字段)

**Interfaces:**
- Consumes: `registers/*.csv` (7 files)
- Produces: `validate_registers.py` — 8 条确定性校验规则，exit code 0=通过, 1=blocker found

- [ ] **Step 1: 更新 evidence.csv Schema（增加 source_grade）**

Read current `registers/evidence.csv` header, then write updated:

```csv
evidence_id,title,source_type,source_name,url_or_path,date_collected,source_grade,direct_quote,importance,related_doc,related_section,summary,confidence,notes
```

New fields:
- `source_grade`: A/B/C/D (来自 market-deep-research 分级标准)
- `direct_quote`: 源文直接引述（Falsifiable Claim 的核心证据）
- `importance`: central/supporting/tangential

- [ ] **Step 2: 编写 evidence JSON Schema**

Write `validators/schemas/evidence.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "evidence",
  "title": "Evidence Record",
  "type": "object",
  "required": ["evidence_id", "title", "source_type", "source_grade", "confidence"],
  "properties": {
    "evidence_id": {
      "type": "string",
      "pattern": "^EV-[A-Z]+-\\d{3}$",
      "description": "Format: EV-{project}-{seq}"
    },
    "source_grade": {
      "type": "string",
      "enum": ["A", "B", "C", "D"],
      "description": "A=政府/监管/财报/检测, B=行业报告/专利, C=品牌PR/电商/协会, D=社交/匿名"
    },
    "confidence": {
      "type": "string",
      "enum": ["高", "中", "低", "未知"]
    },
    "importance": {
      "type": "string",
      "enum": ["central", "supporting", "tangential"]
    },
    "direct_quote": {
      "type": "string",
      "description": "源文直接引述，不是 Agent 改写"
    }
  }
}
```

- [ ] **Step 3: 编写 traceability JSON Schema**

Write `validators/schemas/traceability.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "traceability",
  "title": "Traceability Record",
  "type": "object",
  "required": ["trace_id", "requirement_id", "evidence_id"],
  "properties": {
    "trace_id": {
      "type": "string",
      "pattern": "^T-[A-Z]+-\\d{3}$"
    },
    "requirement_id": {
      "type": "string",
      "pattern": "^REQ-[A-Z]+-\\d{3}$"
    },
    "evidence_id": {
      "type": "string",
      "pattern": "^EV-[A-Z]+-\\d{3}$"
    },
    "validation_item": { "type": "string" },
    "status": {
      "type": "string",
      "enum": ["linked", "verified", "broken"]
    }
  }
}
```

- [ ] **Step 4: 编写 gate-request JSON Schema**

Write `validators/schemas/gate-request.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "gate-request",
  "title": "Gate Approval Request",
  "type": "object",
  "required": ["gate_id", "project_id", "artifacts", "review_status", "validation_status"],
  "properties": {
    "gate_id": { "type": "string", "enum": ["Gate1", "Gate2", "Gate3", "Gate4", "Gate5", "Gate6", "Gate7"] },
    "project_id": { "type": "string" },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["artifact_id", "artifact_type", "version", "review_verdict"],
        "properties": {
          "artifact_id": { "type": "string" },
          "artifact_type": { "type": "string" },
          "version": { "type": "string" },
          "review_verdict": { "type": "string", "enum": ["approved", "conditional", "rejected"] },
          "content_hash": { "type": "string" }
        }
      }
    },
    "validation_status": {
      "type": "object",
      "required": ["registers_check", "traceability_check"],
      "properties": {
        "registers_check": { "type": "boolean" },
        "traceability_check": { "type": "boolean" }
      }
    },
    "decision_options": {
      "type": "array",
      "items": { "type": "string" },
      "description": "选项列表，如 ['批准进入下一阶段', '有条件批准（附条件）', '退回修正']"
    }
  }
}
```

- [ ] **Step 5: 编写 validate_registers.py — 8 条确定性校验**

Write `validators/scripts/validate_registers.py`:

```python
"""台账完整性校验 — 8 条确定性规则。exit code 0 = PASS, 1 = blocker found."""
import csv
import sys
import re
from pathlib import Path

REGISTERS_DIR = Path(__file__).parent.parent.parent / "registers"

def load_csv(name: str) -> list[dict]:
    path = REGISTERS_DIR / name
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))

def validate_id_format(record_id: str, prefix: str) -> bool:
    pattern = rf"^{prefix}-[A-Z]+-\d{{3}}$"
    return bool(re.match(pattern, record_id))

def check_v01(requirements: list[dict], traceability: list[dict]) -> list[str]:
    """每条 P0/P1 requirement 有 ≥1 条 traceability"""
    errors = []
    req_ids_with_trace = {t["requirement_id"] for t in traceability if t.get("requirement_id")}
    for req in requirements:
        if req.get("priority") in ("P0", "P1"):
            if req["requirement_id"] not in req_ids_with_trace:
                errors.append(f"V-01: {req['requirement_id']} (priority={req.get('priority')}) has no traceability")
    return errors

def check_v02(traceability: list[dict], evidence: list[dict]) -> list[str]:
    """traceability 中引用的 evidence_id 存在"""
    errors = []
    ev_ids = {e["evidence_id"] for e in evidence}
    for t in traceability:
        eid = t.get("evidence_id", "").strip()
        if eid and eid not in ev_ids:
            errors.append(f"V-02: traceability {t['trace_id']} references non-existent evidence {eid}")
    return errors

def check_v03(traceability: list[dict], requirements: list[dict]) -> list[str]:
    """traceability 中引用的 requirement_id 存在"""
    errors = []
    req_ids = {r["requirement_id"] for r in requirements}
    for t in traceability:
        rid = t.get("requirement_id", "").strip()
        if rid and rid not in req_ids:
            errors.append(f"V-03: traceability {t['trace_id']} references non-existent requirement {rid}")
    return errors

def check_v04(assumptions: list[dict]) -> list[str]:
    """assumptions 中 confidence=高 但没有 validation_method"""
    errors = []
    for a in assumptions:
        if a.get("confidence") == "高" and not a.get("validation_method", "").strip():
            errors.append(f"V-04: assumption {a.get('assumption_id', '?')} confidence=高 but no validation_method")
    return errors

def check_v05(risks: list[dict]) -> list[str]:
    """risks 中 impact=高 但没有 mitigation"""
    errors = []
    for r in risks:
        if r.get("impact") == "高" and not r.get("mitigation", "").strip():
            errors.append(f"V-05: risk {r.get('risk_id', '?')} impact=高 but no mitigation")
    return errors

def check_v06(evidence: list[dict]) -> list[str]:
    """evidence 的 source_grade 不为空"""
    errors = []
    for e in evidence:
        if not e.get("source_grade", "").strip():
            errors.append(f"V-06: evidence {e['evidence_id']} missing source_grade")
        if e.get("source_grade") not in ("A", "B", "C", "D", ""):
            errors.append(f"V-06: evidence {e['evidence_id']} invalid source_grade: {e.get('source_grade')}")
    return errors

def check_v07(evidence: list[dict], assumptions: list[dict], risks: list[dict],
              decisions: list[dict], requirements: list[dict], traceability: list[dict]) -> list[str]:
    """ID 格式符合规范，无跨文件重复"""
    errors = []
    all_ids = []
    patterns = {
        "evidence": (r"^EV-[A-Z]+-\d{3}$", evidence, "evidence_id"),
        "assumption": (r"^A-[A-Z]+-\d{3}$", assumptions, "assumption_id"),
        "risk": (r"^RISK-[A-Z]+-\d{3}$", risks, "risk_id"),
        "decision": (r"^DEC-[A-Z]+-\d{3}$", decisions, "decision_id"),
        "requirement": (r"^REQ-[A-Z]+-\d{3}$", requirements, "requirement_id"),
        "traceability": (r"^T-[A-Z]+-\d{3}$", traceability, "trace_id"),
    }
    seen = set()
    for label, (pattern, records, key) in patterns.items():
        for rec in records:
            rid = rec.get(key, "").strip()
            if not rid:
                continue
            if not re.match(pattern, rid):
                errors.append(f"V-07: {label} {rid} does not match pattern {pattern}")
            if rid in seen:
                errors.append(f"V-07: duplicate ID {rid}")
            seen.add(rid)
    return errors

def check_v08(decisions: list[dict], requirements: list[dict]) -> list[str]:
    """已批准 artifact 有关联 decision_id — 信息性检查，不强制 block"""
    errors = []
    # 此规则在 Gate 审批阶段由 hw-gate-prep 调用时检查
    # 仅在有 decisions 和 requirements 时输出提示
    if decisions and not requirements:
        errors.append("V-08: INFO — decisions exist but no requirements yet (pre-PRD stage, expected)")
    return errors

def main():
    evidence = load_csv("evidence.csv")
    assumptions = load_csv("assumptions.csv")
    risks = load_csv("risks.csv")
    decisions = load_csv("decisions.csv")
    requirements = load_csv("requirements.csv")
    traceability = load_csv("traceability.csv")

    all_errors = []
    all_errors.extend(check_v01(requirements, traceability))
    all_errors.extend(check_v02(traceability, evidence))
    all_errors.extend(check_v03(traceability, requirements))
    all_errors.extend(check_v04(assumptions))
    all_errors.extend(check_v05(risks))
    all_errors.extend(check_v06(evidence))
    all_errors.extend(check_v07(evidence, assumptions, risks, decisions, requirements, traceability))
    all_errors.extend(check_v08(decisions, requirements))

    if all_errors:
        print(f"VALIDATION FAILED — {len(all_errors)} issues found:")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED — all 8 checks passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 编写 validate_traceability.py**

Write `validators/scripts/validate_traceability.py`:

```python
"""追踪覆盖率校验。exit code 0 = 覆盖率 ≥80%, 1 = 覆盖率不足."""
import csv
import sys
from pathlib import Path

REGISTERS_DIR = Path(__file__).parent.parent.parent / "registers"

def main():
    with open(REGISTERS_DIR / "requirements.csv") as f:
        requirements = list(csv.DictReader(f))
    with open(REGISTERS_DIR / "traceability.csv") as f:
        traceability = list(csv.DictReader(f))

    p0_p1_reqs = [r for r in requirements if r.get("priority") in ("P0", "P1")]
    if not p0_p1_reqs:
        print("No P0/P1 requirements found — nothing to trace")
        sys.exit(0)

    traced_ids = {t["requirement_id"] for t in traceability if t.get("requirement_id")}
    total = len(p0_p1_reqs)
    covered = sum(1 for r in p0_p1_reqs if r["requirement_id"] in traced_ids)
    pct = (covered / total) * 100

    print(f"Traceability coverage: {covered}/{total} ({pct:.0f}%)")
    for r in p0_p1_reqs:
        if r["requirement_id"] not in traced_ids:
            print(f"  UNTRACED: {r['requirement_id']} — {r.get('title', '')}")

    if pct < 80:
        print(f"FAIL: coverage {pct:.0f}% < 80% threshold")
        sys.exit(1)
    else:
        print("PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 7: 编写 validate_gate.py**

Write `validators/scripts/validate_gate.py`:

```python
"""Gate 条件校验 — 检查指定 Gate 的所有 artifact 是否已通过 review."""
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: validate_gate.py <gate_request.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        gate = json.load(f)

    errors = []
    for art in gate.get("artifacts", []):
        if art["review_verdict"] == "rejected":
            errors.append(f"{art['artifact_id']}: rejected by reviewer — cannot proceed")
        if art["review_verdict"] == "conditional":
            errors.append(f"{art['artifact_id']}: conditional approval — verify conditions met")

    if not gate.get("validation_status", {}).get("registers_check"):
        errors.append("registers_check: FAILED — run validate_registers.py first")
    if not gate.get("validation_status", {}).get("traceability_check"):
        errors.append("traceability_check: FAILED — run validate_traceability.py first")

    if errors:
        print(f"GATE BLOCKED — {len(errors)} issues:")
        for err in errors:
            print(f"  {err}")
        sys.exit(1)
    else:
        print(f"GATE {gate['gate_id']}: READY for human approval")
        print(f"Decision options: {gate.get('decision_options', [])}")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 8: 运行校验脚本验证语法**

```bash
cd validators/scripts
python3 -c "import validate_registers; print('validate_registers: syntax OK')"
python3 -c "import validate_traceability; print('validate_traceability: syntax OK')"
python3 -c "import validate_gate; print('validate_gate: syntax OK')"
```

Expected: three "syntax OK" messages.

- [ ] **Step 9: 用现有台账测试 validate_registers.py**

```bash
cd /Users/kevinyu/产品经理文档模版
python3 validators/scripts/validate_registers.py
```

Expected: PASS (现有台账为空，不应有违规).

- [ ] **Step 10: Commit**

```bash
git add validators/ registers/evidence.csv
git commit -m "feat(phase-0): add CSV schemas, evidence source_grade field, and Python validators (8 rules)"
```

---

### Task 0.4: 模板更新 — 摘要章节

**Files:**
- Modify: `templates/01_产品市场与机会研究报告.md` (增加"摘要"章节)
- Modify: `templates/09_竞品研究分析报告.md` (增加"摘要"章节)
- Modify: `templates/10_用户研究与VOC分析报告.md` (增加"摘要"章节)
- Create: `templates/17_产品合规研究报告.md`
- Create: `templates/18_专利格局分析报告.md`

**Interfaces:**
- Consumes: `docs/architecture.md` 六-输出格式 (摘要 ≤500字, 输入来源表)
- Consumes: market-deep-research audit — 报告含 "What Would Change the Conclusion" 章节
- Produces: 5 个更新的模板文件

- [ ] **Step 1: 在 01_产品市场与机会研究报告.md 开头增加摘要章节**

Read current file, then insert after title line:

```markdown
## 摘要（≤500字）

> **面向 PM Agent 的下游消费**。CSV 是权威记录，此摘要为阅读导航。

### 对路由有影响的发现
- 

### 对产品定义有约束的发现
- 

### 需要 PM 决策的开放问题
- 

### 什么新证据会改变结论
- 
```

- [ ] **Step 2: 在 09_竞品研究分析报告.md 增加相同摘要章节**

Same structure as Step 1.

- [ ] **Step 3: 在 10_用户研究与VOC分析报告.md 增加相同摘要章节**

Same structure as Step 1.

- [ ] **Step 4: 新建 17_产品合规研究报告.md**

Write `templates/17_产品合规研究报告.md` using product-standards 输出结构：

```markdown
# 17_产品合规研究报告

## 输入/输出

### 方法说明
产品合规研究报告用于明确产品在中国市场（及目标出口市场）的监管准入要求、适用标准清单、合规定级和认证路径。

### 内容说明
- 输入：product_profile（32 合规模块激活判定）、目标市场列表
- 输出：standards_map（逐模块标准匹配）、compliance_profile（must/should/comply 定级）、认证路径图

---

## 摘要（≤500字）

### 强制合规项（must）
- 

### 推荐合规项（should）
- 

### 参考合规项（comply）
- 

### 认证路径关键里程碑
- 

### 什么新证据会改变结论
- 

---

## 1. 产品合规画像

### 1.1 基本信息
- 产品名称：
- 产品品类：
- 目标市场：
- 供电方式：
- 通信方式：

### 1.2 32 合规模块激活判定

| 模块ID | 制度 | 激活状态 | 判定依据 |
|--------|------|---------|---------|
| A01_CCC | 强制性产品认证 | activated / excluded / uncertain | |
| M01_electrical | 电器安全 | | |
| M02_EMC | 电磁兼容 | | |
| M03_SRRC | 无线电型号核准 | | |
| M04_battery | 电池安全 | | |
| M05_motor | 电机/运动部件安全 | | |
| M07_fire | 防火/建筑构件安全 | | |
| M08_security | 安防/防盗 | | |
| ... | ... | | |

---

## 2. 标准地图（standards_map）

| 模块ID | 标准编号 | 标准名称 | 标准类型 | 状态 | 获取层级 | URL |
|--------|---------|---------|---------|------|---------|-----|
| M01 | GB 4943.1 | 音视频、信息技术和通信技术设备 安全要求 | GB 强制性 | 现行 | L1 免费 | https://openstd.samr.gov.cn/... |
| | | | | | | |

### 模块覆盖率
- 激活模块数: N
- 已匹配标准模块数: M
- 覆盖率: M/N (%)
- Gap 模块: [列出未匹配到标准的模块及替代方案]

---

## 3. 合规档案（compliance_profile）

### 3.1 合规定级

| 标准编号 | 定级 | 适用范围 | 核心指标 | 限值 | 验证方式 |
|---------|------|---------|---------|------|---------|
| GB 4943.1 | must | 整机（含电源电路） | 电气间隙 | ≥Xmm | 型式试验 |
| | | | | | |

定级说明：
- **must**：法规强制，不满足无法上市
- **should**：推荐性标准或行业惯例，不满足影响竞争力
- **comply**：参考标准，声明即符合或暂无强制要求

### 3.2 认证路径

| 认证类型 | 流程步骤 | 预计周期 | 关键节点 | 费用估算 |
|---------|---------|---------|---------|---------|
| CCC | 型式试验 → 工厂检查 → 获证 → 年度监督 | X 周 | | ¥X |
| SRRC | | | | |

---

## 4. 输入来源与完整性

| 输入项 | 来源文档/证据 | 状态 | 对合规判断影响 | 缺口处理 |
|-|-|-|-|-|
| 产品画像 | product_profile.json | 已完成/阶段性/缺失 | 高/中/低 | |
| 标准检索 | standards_map.json | | | |
| 竞品合规参考 | hw-competitive-analysis 输出 | | | |
| | | | | |

---

## 5. 风险与不确定性

| 风险 | 影响 | 缓解 |
|------|------|------|
| 模块 XX 激活状态 uncertain | 可能遗漏合规要求 | 建议 XX 部门确认 |
| 标准 XX 即将实施 | 上市时间可能与新标准生效冲突 | 跟踪标准发布时间线 |
```

- [ ] **Step 5: 新建 18_专利格局分析报告.md**

Write `templates/18_专利格局分析报告.md`:

```markdown
# 18_专利格局分析报告

## 输入/输出

### 方法说明
专利格局分析报告用于了解关键技术领域的专利布局态势、识别阻塞风险和空白机会区域。

### 内容说明
- 输入：关键技术领域定义、核心竞品清单、技术关键词
- 输出：专利地图、阻塞风险标记、空白区域识别、竞品专利策略分析
- **边界**：本报告仅做格局分析，不构成法律意见。FTO（自由实施）分析和侵权判断需由专业专利律师完成。

---

## 摘要（≤500字）

### 关键发现
- 

### 阻塞风险
- 

### 空白/机会区域
- 

### 需要法务判断的问题
- 

### 什么新证据会改变结论
- 

---

## 1. 技术领域定义

- 核心技术领域：
- 检索关键词（中/英）：
- IPC 分类号：
- 检索时间范围：

## 2. 专利地图

### 2.1 总体态势

| 指标 | 数值 |
|------|------|
| 相关专利总数 | |
| 近 5 年申请趋势 | |
| 主要申请人 Top 10 | |
| 主要申请国家/地区 | |

### 2.2 技术分布

| 技术分支 | 专利数量 | 主要申请人 | 活跃程度 |
|---------|---------|-----------|---------|
| | | | 高/中/低 |

### 2.3 核心专利识别

| 专利号 | 标题 | 申请人 | 申请日 | 法律状态 | 被引次数 | 相关性 |
|--------|------|--------|--------|---------|---------|--------|
| | | | | | | 高/中/低 |

## 3. 竞品专利策略

| 竞品 | 相关专利数 | 核心布局领域 | 诉讼/许可历史 | 对我方影响 |
|------|-----------|-------------|-------------|-----------|
| | | | | 阻塞/需关注/低风险 |

## 4. 阻塞风险与回避方向

### 4.1 阻塞专利

| 专利号 | 阻塞的权利要求 | 规避设计可行性 | 需法务评估 |
|--------|---------------|---------------|-----------|
| | | 高/低 | 是/否 |

### 4.2 空白区域

| 技术方向 | 专利密度 | 进入机会 | 风险提示 |
|---------|---------|---------|---------|
| | 低/中/高 | | |

## 5. 输入来源与完整性

| 输入项 | 来源/数据库 | 状态 | 局限 |
|-|-|-|-|
| 专利检索 | | 已完成/阶段性 | |
| 法律状态核实 | | | 部分专利法律状态可能存在延迟 |
| 竞品专利匹配 | | | |

## 6. 免责声明

本报告由 AI Agent 基于公开专利数据库自动生成，仅用于产品规划和研发决策参考。
不构成任何形式的法律意见、FTO 分析或侵权判断。涉及具体专利的法律风险评估，
请咨询专业专利律师。
```

- [ ] **Step 6: 验证模板完整性**

```bash
echo "=== 摘要章节检查 ==="
for f in templates/01_产品市场与机会研究报告.md templates/09_竞品研究分析报告.md templates/10_用户研究与VOC分析报告.md; do
  grep -q "摘要（≤500字）" "$f" && echo "  $f: ✓" || echo "  $f: ✗ MISSING"
done
echo "=== 新增模板检查 ==="
for f in templates/17_产品合规研究报告.md templates/18_专利格局分析报告.md; do
  [ -f "$f" ] && echo "  $f: ✓" || echo "  $f: ✗ MISSING"
done
```

Expected: all ✓.

- [ ] **Step 7: Commit**

```bash
git add templates/
git commit -m "feat(phase-0): add 摘要 chapter to research templates; create compliance and patent report templates"
```

---

### Task 0.5: SKILL_TEMPLATE.md — Skill 编写范式

**Files:**
- Create: `skills/SKILL_TEMPLATE.md`

**Interfaces:**
- Consumes: pm-skills 审计结论（原 23 个 + market-deep-research + product-standards）
- Produces: 所有 16 个 SKILL.md 的编写规范

- [ ] **Step 1: 编写 SKILL_TEMPLATE.md**

Write `skills/SKILL_TEMPLATE.md`:

```markdown
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

```markdown
# ✗ 禁止: 只有高层指导，没有可执行步骤
## Instructions
1. 分析市场情况
2. 写出报告

# ✗ 禁止: 输出模板用引用代替
## Output
参考 templates/01_xxx.md

# ✗ 禁止: Quality Bar 模糊
## Quality Bar
- 报告质量要高
```

## 正例（目标模式）

```markdown
# ✓ 目标: 每步有输入/操作/检查点
## Instructions

### Step 1: 加载项目上下文
- 输入：读取 `project_profile.json` 和 Gate 1 审批记录
- 操作：提取目标市场、产品品类、技术关键词
- 检查点：9 个研究维度中至少确定 6 个可检索

### Step 2: 证据收集与分级
- 输入：Step 1 的关键词列表
- 操作：对每个维度执行搜索 → 提取 falsifiable claim → 标记 source_grade
- 检查点：每条 evidence 记录包含 evidence_id, direct_quote, source_grade, importance
```
```

- [ ] **Step 2: 验证模板自指一致性**

检查 SKILL_TEMPLATE.md 本身是否满足它定义的 9 章节结构。应全部满足。

- [ ] **Step 3: Commit**

```bash
git add skills/SKILL_TEMPLATE.md
git commit -m "feat(phase-0): write SKILL_TEMPLATE.md — skill writing paradigm from pm-skills audit"
```

---

### Task 0.6: Phase 0 收尾 — 集成验证

**Files:**
- Modify: `README.md` (更新项目说明)
- Verify: 全部 Phase 0 产出的一致性

**Interfaces:**
- Consumes: Task 0.1-0.5 的全部产出
- Produces: Phase 0 完成确认

- [ ] **Step 1: 更新 README.md 项目说明**

在 README.md 顶部增加：

```markdown
# 智能硬件 PM Agent

> 将产品经理文档模版包的方法论，实现为可独立运行的 3-Agent 协作系统。

## 快速开始

1. 加载 AGENTS.md 到 Claude Code（自动，通过 SessionStart hook）
2. 新项目：触发 `hw-intake` → 引导式访谈 → 路由判定 → Gate 1 审批
3. 研究阶段：各 Researcher Skill 串行执行，产出研究报告 + evidence.csv
4. 规划阶段：PM Skills 基于批准的研究报告产出产品文档
5. 每个 Gate 前运行 `python3 validators/scripts/validate_registers.py` 确保台账完整性

## 项目结构

| 目录 | 用途 |
|------|------|
| `skills/` | 16 个 Agent Skills，按 Researcher/PM/Reviewer/Shared 分组 |
| `templates/` | 18 个 Markdown 文档模板 |
| `registers/` | 7 个 CSV 台账，evidence.csv 是唯一真相源 |
| `validators/` | JSON Schema + Python 确定性校验脚本 |
| `adapters/feishu/` | Phase 3 飞书双向同步契约 |
| `docs/` | 设计文档：architecture.md + pm-skills 审计 |

## 当前状态

- Phase 0: ✅ 基础搭建完成
- Phase 1: ⬜ L1 MVP — 8 个核心 Skills + 端到端测试
- Phase 2: ⬜ L2 + 完整 16 Skills
- Phase 3: ⬜ 飞书协作界面接入
- Phase 4: ⬜ L3 + 独立应用封装
```

- [ ] **Step 2: Phase 0 完整性检查**

```bash
echo "=== Phase 0 交付物检查 ==="
echo "--- 目录结构 ---"
for d in skills/researcher skills/pm skills/reviewer skills/shared validators/schemas validators/scripts adapters/feishu; do
  [ -d "$d" ] && echo "  $d: ✓" || echo "  $d: ✗ MISSING"
done
echo "--- AGENTS.md ---"
[ -f AGENTS.md ] && echo "  AGENTS.md: ✓ ($(wc -l < AGENTS.md) lines)" || echo "  ✗"
echo "--- SKILL_TEMPLATE.md ---"
[ -f skills/SKILL_TEMPLATE.md ] && echo "  SKILL_TEMPLATE.md: ✓" || echo "  ✗"
echo "--- Validators ---"
for f in validators/scripts/validate_registers.py validators/scripts/validate_traceability.py validators/scripts/validate_gate.py; do
  [ -f "$f" ] && echo "  $f: ✓" || echo "  $f: ✗"
done
echo "--- Schemas ---"
for f in validators/schemas/evidence.schema.json validators/schemas/traceability.schema.json validators/schemas/gate-request.schema.json; do
  [ -f "$f" ] && echo "  $f: ✓" || echo "  $f: ✗"
done
echo "--- Templates (摘要章节) ---"
for f in templates/01_产品市场与机会研究报告.md templates/09_竞品研究分析报告.md templates/10_用户研究与VOC分析报告.md; do
  grep -q "摘要" "$f" && echo "  $f: ✓" || echo "  $f: ✗"
done
echo "--- New Templates ---"
for f in templates/17_产品合规研究报告.md templates/18_专利格局分析报告.md; do
  [ -f "$f" ] && echo "  $f: ✓" || echo "  $f: ✗"
done
```

Expected: all ✓.

- [ ] **Step 3: AGENTS.md 自举测试**

在 Claude Code 中加载 AGENTS.md 后，Agent 应能正确回答：
- "我是什么角色？" → 描述 3-Agent 模型和边界
- "我的质量底线是什么？" → 列举 6 条质量规则
- "台账什么时候写入？" → 区分流式写入 vs 门禁写入

- [ ] **Step 4: 校验脚本端到端测试**

```bash
cd /Users/kevinyu/产品经理文档模版
echo "--- Test: validate_registers.py on empty registers ---"
python3 validators/scripts/validate_registers.py && echo "PASS" || echo "Check errors above"
echo "--- Test: validate_traceability.py on empty registers ---"
python3 validators/scripts/validate_traceability.py && echo "PASS" || echo "Check errors above"
```

Expected: PASS / "No P0/P1 requirements found".

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs(phase-0): update README with project status and quickstart; Phase 0 complete"
git push origin main
```

---

## Phase 1：L1 MVP — 本地闭环（~1-2 周）

**目标**: Claude Code 内跑通 L1 项目完整流程。**不涉及飞书**。
**退出条件**: L1 项目启动→PRD→验证完整链路通过，traceability 链路闭环，所有 Gate 有人工确认。

### Task 1.1: hw-intake（项目启动 + 路由）

**Skill**: `skills/pm/hw-intake/SKILL.md`
**输入**: 项目资料包 + source-manifest.json
**输出**: 启动卡 + 路由判定(L1/L2/L3) + Gate 1 简报 + 任务包
**台账**: decisions.csv（仅 Gate 1 人工批准后写入）
**参考**: `templates/00_项目启动卡.md`, `docs/16_项目启动引导式访谈与路由信息补全方案.md`
**方法论**: market-deep-research 的 Intent Card + User Confirmation 模式

### Task 1.2: hw-market-study（市场研究）

**Skill**: `skills/researcher/hw-market-study/SKILL.md`
**输入**: 启动卡 + 行业线索
**输出**: 市场研究报告（含摘要 + 输入来源表）
**台账**: evidence.csv（含 source_grade + direct_quote）, assumptions.csv
**模板**: `templates/01_产品市场与机会研究报告.md`
**方法论**: market-deep-research 的 9-dimension framework + Falsifiable Claim Extraction

### Task 1.3: hw-competitive-analysis（竞品分析）

**Skill**: `skills/researcher/hw-competitive-analysis/SKILL.md`
**输入**: 市场研究输出的核心竞品清单
**输出**: 竞品研究报告（含摘要 + 输入来源表）
**台账**: evidence.csv, assumptions.csv
**模板**: `templates/09_竞品研究分析报告.md`

### Task 1.4: hw-user-research（用户研究）

**Skill**: `skills/researcher/hw-user-research/SKILL.md`
**输入**: 候选用户人群 + VOC 线索
**输出**: 用户研究报告（含摘要 + 输入来源表）
**台账**: evidence.csv, assumptions.csv
**模板**: `templates/10_用户研究与VOC分析报告.md`

### Task 1.5: hw-review（独立审查）— Phase 1 集成

**Skill**: `skills/reviewer/hw-review/SKILL.md`
**输入**: Researcher 报告或 PM 文档 + 台账
**输出**: findings（severity: blocker/high/medium/low + required_action: must_fix/suggest/submit_decision）
**台账**: risks.csv（如发现新风险）
**方法论**: 3-lens adversarial verification（market-deep-research）+ product-standards 的 PM 反馈模式

### Task 1.6: hw-prd（产品需求文档）

**Skill**: `skills/pm/hw-prd/SKILL.md`
**输入**: 产品定义 + 约束
**输出**: PRD（四模块：功能/软件/硬件/结构）+ requirements.csv + traceability.csv
**台账**: requirements.csv, traceability.csv
**模板**: `templates/05_PRD_产品需求文档.md`, `templates/12_L1_轻量产品定义_PRD合并文档.md`

### Task 1.7: hw-validation-plan（验证计划）

**Skill**: `skills/pm/hw-validation-plan/SKILL.md`
**输入**: PRD + assumptions.csv + risks.csv
**输出**: 验证计划
**台账**: traceability.csv（更新验证项关联）
**模板**: `templates/06_验证计划.md`

### Task 1.8: hw-gate-prep（Gate 准备）

**Skill**: `skills/pm/hw-gate-prep/SKILL.md`
**输入**: 各阶段产物 + Reviewer findings
**输出**: Gate 摘要 + 选项分析 + gate-request.json
**台账**: decisions.csv（人工确认后写入）
**依赖**: validate_registers.py + validate_gate.py 全部通过

### Task 1.9: L1 端到端测试

用真实 L1 项目（如"无线链式开窗机指定电机降本"）跑通完整流程：
启动→路由→市场研究→竞品分析→用户研究→PRD→验证计划→Gate

**验证点**：
- [ ] 每个文档产出前经过 hw-review 审查
- [ ] traceability 链路：P0 需求 → evidence → 验证
- [ ] 所有 Gate 有人工确认记录
- [ ] Python 校验脚本在每个 Gate 前通过

---

## Phase 2：L2 + 完整 Skills（~2 周）

**退出条件**: L2 项目完整跑通，16 个 Skills 全部可用，跨项目学习机制工作。

### Task 2.1-2.8: 补齐剩余 8 个 Skills

| Task | Skill | 角色 | 模板 |
|------|-------|------|------|
| 2.1 | hw-compliance-research | Researcher | 17_产品合规研究报告.md (product-standards 管道架构) |
| 2.2 | hw-patent-analysis | Researcher | 18_专利格局分析报告.md |
| 2.3 | hw-product-strategy | PM | 14_产品规划报告.md (三定+MVP+路线图) |
| 2.4 | hw-mrd-brd | PM | 02_MRD + 03_BRD / 07_合并版 |
| 2.5 | hw-product-definition | PM | 04_产品定义文档.md |
| 2.6 | hw-red-team | Reviewer | (杀伤性假设 + 最便宜验证方案) |
| 2.7 | hw-retro | Shared | 11_项目复盘与方法沉淀记录.md |
| 2.8 | hw-handoff | Shared | (按硬件/固件/APP/测试/质量/供应链/售后拆包) |

### Task 2.9: L2 流程验证

用真实 L2 项目（如 CWLS 开窗机新 SKU）跑通。

### Task 2.10: 跨项目学习机制

method_learnings.csv 检索 + 新项目启动时自动加载关联教训。

### Task 2.11: 任务包自动生成

hw-intake 输出中增加 L1/L2/L3 差异化的任务清单。

---

## Phase 3：飞书协作界面接入（~2-3 周）

**目标**: 增加 Feishu Adapter 层，Agent 产出同步到飞书。Agent Core 和 Skills 逻辑不变。

### Task 3.1: 文档双向同步引擎

`adapters/feishu/doc-sync.md` — Markdown ↔ 飞书文档同步契约：
- AI 完成报告 → 自动同步到飞书文档（草稿状态）
- 人类 PM 在飞书中评论/修改
- AI 检测更新 → 拉回 → 合并（人类修改优先）
- 冲突时不覆盖，通知 PM

### Task 3.2: 审批流程集成

`adapters/feishu/approval-sync.md` — Gate → 飞书审批：
- AI 生成 Gate 摘要 → 发起飞书审批（附带文档链接 + 决策选项）
- 人类 PM 审批 → 回写 decisions.csv
- 退回时读取退回原因 → 修正 → 重新发起

### Task 3.3: IM 通知

`adapters/feishu/notification-spec.md` — 事件 → 消息卡片：
- Reviewer 发现 blocker → 推送卡片给 PM
- Gate 审批请求 → 通知审批人
- 任务逾期 → 提醒

### Task 3.4: Base 共享 + 任务同步

CSV ↔ Base 表同步 + 任务包 → 飞书任务。

### Task 3.5: 飞书集成端到端测试

用 Phase 2 L2 项目重新跑，验证整个 AI→飞书→AI 循环。

---

## Phase 4：L3 + 生产化（按需）

| Task | 说明 |
|------|------|
| 4.1 L3 完整流程 | 全部 11 份文档端到端验证 |
| 4.2 多项目并行 | Base 项目总览、风险仪表盘 |
| 4.3 运行指标 | 效率/质量/决策/交付/Agent 指标 |
| 4.4 独立应用封装 | 从 Claude Code 解耦，独立部署 |

---

## 风险跟踪

| 风险 | Phase | 缓解 |
|------|-------|------|
| Skills 在 Claude Code 中行为不稳定 | 1-2 | 每个 Skill 有可检查完成条件；Reviewer 独立验证 |
| 上下文窗口不足 | 1-2 | 摘要 ≤500 字设计；PM 先读摘要再按需回查 |
| 台账数据漂移 | 1-2 | Gate 前强制运行校验脚本 |
| 飞书集成复杂度导致延期 | 3 | Adapter 隔离在独立模块，不阻塞 Phase 1-2 |
| 人工 Gate 过多导致效率低 | 1-4 | L1/L2/L3 分级裁剪 Gate 数量 |
