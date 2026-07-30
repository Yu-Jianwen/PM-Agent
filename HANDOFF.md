# 会话交接

> 更新时间：2026-07-30

## 线程一：产品项目 — 无线链式开窗机新 SKU

> 项目编号：`PRJ-CWLS-MANUAL-MODE-001`
> 已批准路线：`L2 产品衍生`
> 人工审批状态：**Gate 1 已由余健文批准**

- **任务**：在手动模式下识别用户操作方向，并记录/计算手动移动行程。方案：增加霍尔传感器检测链轮转动方向 → 计算手动移动距离。涉及功能、软件、交互、传感器、电控。创建新 SKU。
- **已完成**：启动资料接入、引导式路由访谈、L2 判定、Gate 1 审批、L2 任务拆解、产品定义 v0.1 初稿（2026-07-22）、飞书资料读取（规格书/PRD/硬件方案/电控梳理/立项报告/太阳能测试等）
- **卡在哪**：PRD v0.1 工作草案进行中，未冻结；专项证据收集未完成；产品定义 v1.0 正式评审未完成
- **下一步**：完成 PRD v0.1 草案 → 补充霍尔传感器方案验证 → 产品定义 v1.0 评审 → PRD 冻结 → 开发
- **踩坑**：暂无

---

## 线程二：Agent 架构设计 — 智能硬件 PM Agent

> 设计版本：`PM-Agent-Design-v0.3`
> 方案文档：[docs/architecture.md](docs/architecture.md) v1.2
> 飞书 Wiki：https://qcn5kzbeuy4o.feishu.cn/wiki/ZZtBwGYYQi7CawkVMxccpGc2nWb
> GitHub：https://github.com/Yu-Jianwen/PM-Agent

### 我们做了什么

**pm-skills 全量审计**：深度阅读 23/68 个 phuryn/pm-skills 的源码。提取了成熟 Skill 设计范式。结论：约 50% 方法论可复用，但输出模板需全部硬件化重写（四模块拆分、BOM、认证、供应链等维度）。

**3-Agent 架构**：确定了 Researcher（5 skills）→ PM（7 skills）→ Reviewer（2 skills）+ 2 shared = 16 skills 的三层模型。

**Researcher 五个研究领域**：市场（含技术趋势+产业链）、用户（多角色链）、竞品（拆机+BOM+供应链）、合规（按 L1/L2/L3 分级）、专利（格局分析，不做法律判断）。

**关键边界**：技术可行性评估属于开发团队（PRD 后），不是 Researcher 桌面研究。专利分析只做格局，不做 FTO 意见。

**Researcher 双输出**：完整报告（给人）+ ≤500字摘要 + evidence.csv（给 PM Agent）。CSV 是权威记录，报告不能润色证据质量。PM 做输入检查时只看 CSV。

**台账机制**：traceability.csv 为中心 JOIN 表。流式写入（证据/假设/风险），增量关联，Python 脚本做 8 条确定性校验。

**Feishu 定位修正**：飞书不是 Runtime，是"人机协作界面"。Claude Code 是唯一 Runtime。Feishu 提供文档双向同步、审批、IM 通知、Base 共享、任务同步。

**market-deep-research v1.1.0 深度审计（新增）**：
- 提取了 10 个可复用方法论，其中 5 个复用度 ≥90%：
  - **证据分级体系 A/B/C/D** → evidence.csv 的 source_grade 字段
  - **Falsifiable Claim 提取规则** → Researcher 的证据写入规范（5 条规则 + 4 种失败模式）
  - **3-Lens 对抗性验证** → Reviewer 的 hw-review 新增 evidence 维度系统化方法
  - **语义去重** → evidence.csv 写入前 fuzzy dedup
  - **阶段审计模板** → 统一所有 Gate 的前置检查
- 中国市场特殊注意事项（咨询报告冲突/政府 vs 行业/品牌自述/电商偏差/区域差异）直接适用

**product-standards 深度审计（新增，替换之前的 gb-convert 误判）**：
- 用户指出合规研究应参考 https://github.com/Yu-Jianwen/product-standards-skill
- 这是一个完整的 4 阶段管道（Phase 0→1→Gate→2→3a→3b），不是简单的 PDF 转换工具
- 核心资产：
  - **32 合规模块清单**（9A 品类准入 + 19B 属性触发 + 4C 标识标签）
  - **多 Agent 并行检索架构**（Analyst → GB_Retriever/TB_Retriever/SUPP_Retriever 并行 → Validator）
  - **合规定级方法**（must/should/comply）+ 认证路径图
  - **试验五要素输出**（方法/条件/设备/判定/样品）
  - **PM 自然语言反馈机制**（PM 不编辑文件，Agent 更新 pm_action）
  - **四级深度分级**（discover/comply/test/full）→ 映射到 L1/L2/L3 流程
- hw-compliance-research 将以 product-standards 的管道架构为设计基础

**Skill 设计范式更新**：从原来的 Purpose→Context→Instructions→Output→Best Practices→Further Reading，新增三个维度：Quality Bar（最低质量标准）、Operating Principles（操作原则）、Tool Integration（工具链集成）

### 当前卡在哪

1. 人类 PM 介入节点（Gate 位置）待确认
2. 跨项目学习（method_learnings 自动检索）待设计
3. 专利数据库接入方式待定
4. PM Agent 分阶段 vs 一次加载待用户确认

### 下一步

1. 确认开放问题
2. 编写 AGENTS.md（Agent System Prompt）
3. 编写 SKILL_TEMPLATE.md（含新增三个维度）
4. 编写首批 Skills（Phase 1: 8 个 L1 核心 Skills）
5. 迁移 mvp-1 校验器（含新增 fuzzy dedup 检查）

### 踩过的坑

- **技术可行性评估放错位置**：初版放在 Researcher 领域，经讨论确认是开发团队的工程判断（PRD 之后）。Researcher 只做技术趋势和产业链（属市场研究）。
- **pm-skills 不是拿来就用**：输出模板完全软件导向，即使方法论可复用也需硬件化重写。
- **不要一个 Agent 干所有事**：Researcher/PM/Reviewer 认知活动不同，强行合并会导致角色混淆和无法自审。
- **台账写入时序很重要**：证据/假设/风险必须流式写入（不能等阶段末批处理），决策必须人工确认后写入。
- **Feishu 不是 Runtime**：初版将飞书设计为独立 Runtime，经讨论修正为"人机协作界面"层，通过 Feishu Adapter 双向同步。
- **"gd-convert"是误判**：用户实际指的是 product-standards skill（https://github.com/Yu-Jianwen/product-standards-skill），一个完整的 4 阶段合规研究管道。初版错误地将其理解为 PDF 转换工具 `gb-convert`，经用户纠正后重新审计并更新方案。
