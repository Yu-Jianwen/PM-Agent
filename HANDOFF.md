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

> 设计版本：`PM-Agent-Design-v1.0`
> 方案文档：[docs/architecture.md](docs/architecture.md) v1.2
> 使用说明：[使用说明.md](使用说明.md)
> 飞书 Wiki：https://qcn5kzbeuy4o.feishu.cn/wiki/ZZtBwGYYQi7CawkVMxccpGc2nWb
> GitHub：https://github.com/Yu-Jianwen/PM-Agent

### 已完成

**Phase 0 — 基础搭建**：目录结构、AGENTS.md（134 行）、SKILL_TEMPLATE.md（195 行）、3 个 JSON Schema + 3 个 Python 校验脚本（8 条确定性规则）、模板更新（合规+专利 2 个新增）

**Phase 1 — L1 MVP**：8 个核心 Skills（5,420 行）+ L1 E2E 测试（CWLS 电机降本，4/4 100% traceability，8/8 校验通过）

**Phase 2 — L2 完整**：8 个剩余 Skills（6,787 行）+ 跨 Skill 契约审计（27 个问题发现并修复）+ L2 E2E 测试（CWLS 开窗机新 SKU，100% traceability，8/8 校验通过）

**L3 E2E — 全流程**：SWCR 智能窗户清洁机器人，13 条 evidence + 7 个 Gate（全 approved）+ 12 requirements + 14 traceability + 3 method_learnings，8/8 校验通过

**总交付**：16 Skills · 12,207 行 · 3 级 E2E 测试数据 · 使用说明.md

### 卡在哪

无阻塞项。Phase 0-2 + L3 全部完成。Phase 3（飞书集成）和 Phase 4（独立应用封装）由用户决定暂不执行。

### 下一步

1. 实际项目中使用 Agent 系统，收集反馈
2. 根据反馈迭代 Skills 方法论
3. 用户确认时机后启动 Phase 3 飞书集成
4. 用户确认时机后启动 Phase 4 独立应用封装

### 踩过的坑

- **技术可行性评估放错位置**：初版放在 Researcher 领域，经讨论确认是开发团队的工程判断（PRD 之后）。Researcher 只做技术趋势和产业链（属市场研究）。
- **pm-skills 不是拿来就用**：输出模板完全软件导向，即使方法论可复用也需硬件化重写。
- **不要一个 Agent 干所有事**：Researcher/PM/Reviewer 认知活动不同，强行合并会导致角色混淆和无法自审。
- **台账写入时序很重要**：证据/假设/风险必须流式写入（不能等阶段末批处理），决策必须人工确认后写入。
- **Feishu 不是 Runtime**：初版将飞书设计为独立 Runtime，经讨论修正为"人机协作界面"层，通过 Feishu Adapter 双向同步。
- **"gd-convert"是误判**：用户实际指的是 product-standards skill（https://github.com/Yu-Jianwen/product-standards-skill），一个完整的 4 阶段合规研究管道。初版错误地将其理解为 PDF 转换工具 `gb-convert`，经用户纠正后重新审计并更新方案。
