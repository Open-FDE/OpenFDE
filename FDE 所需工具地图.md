# FDE 所需工具地图 · AI-native 交付底座 & 客户 AI 选型地图

> 整理日期：2026-06-30 · 数据来自 GitHub 实查（star/许可证为 2026 年中近似值，对外分发前以仓库 LICENSE 为准）
> **两类读者，一张图：**
> · **FDE 个人 / 团队（交付侧）**——当成"AI-native 团队的操作系统"：每一步用什么工具、配什么模型/硬件、怎么用 agent 舰队放大产能。
> · **客户 / 企业（采购 & 自建侧）**——当成"AI 选型与自建地图"：看清有哪些选择、评估自己缺什么、知道该向供应商要什么、避免掉进"试点炼狱"。

---

## 面向客户：怎么用这张图（采购 & 自建视角）

这张图不只给做交付的 FDE 看——**如果你是要落地 AI 的企业**，它是一份中立的选型底图：

1. **看清全景，别被单一叙事带偏**：AI 落地涉及模型 / 工具 / 硬件 / 全流程多层，先看清有哪些选择，再判断供应商给的方案是不是"一根 API 打天下"。
2. **自评缺口**：对照你现在的栈，哪一层空着、哪一层薄（数据接入？带权限的 RAG？eval？可观测？）。
3. **提对要求**：知道该向供应商 / FDE 团队要什么——**开源可控、air-gapped / 信创（数据不出域）、带权限与审计、不被锁定、能沉淀成你自己的可复用资产**（连接器 / 模板 / eval），而不是一次性交付。
4. **避坑（别被漂亮 demo 忽悠）**：demo 跑通 ≠ 能用。盯住"从 demo 到生产"的硬骨头——权限、审计、eval、脏数据、采用；把**验收线定成"被真实用起来 + 业务指标变好 + 且持续维持"**，而不是"演示通过即成功"。
5. **判断路线**：自建 / 采购 / 找 FDE 团队——数据敏感、跨遗留系统、要端到端对结果负责的场景，才值得上 FDE；常规场景用成熟产品即可。

> 想系统了解"不同规模、不同行业的客户该怎么被服务、怎么选路线"，见配套的 **[FDE 实战蓝皮书](./FDE%20实战蓝皮书.md)**。

---

## 核心命题：AI-native FDE 团队 = 小人类核心 + agent 舰队

传统乙方的逻辑是"每个职能配一个人"——一个 SDR、一个设计师、几个前后端、一个测试、一个运维、一个客服。客户越多、需求越复杂，人越多，毛利越薄，最后退化成低毛利服务。

**AI-native FDE 团队的逻辑相反**：

```
                      ┌─────────────────────────────────────┐
   小的人类核心  ──▶  │  判断 · 关系 · 架构 · 取舍 · 对结果负责  │
   (4C 全占的少数人)   └─────────────────────────────────────┘
        │ 编排
        ▼
   一支 agent 舰队  ──▶  执行 · 规模 · 重复劳动 · 7×24
   (SDR/discovery/coding/ops/support agents)
        │ 沉淀
        ▼
   产品化底座  ──▶  每次交付都变成团队共享的可复用资产/产品（50% 利润投这里）
```

三条由此推出的判断：
1. **人不随客户数线性增长。** 过去"一个职能=一个人"，现在"一个人 lead + 一群 agent 干活"。团队规模与客户数解耦，这正是 Palantir「产品化阈值」（前 1-3 个客户深度定制，之后每个客户定制度递减）的 AI 实现。
2. **工具地图 = agent 舰队的运行底座。** 下面每一类工具，不是给某个人用的，而是团队的 agent 跑在上面、或团队用来编排 agent 的基础设施。
3. **团队的护城河在纵轴（产品化底座），不在横轴。** 横轴让团队"把这一单交付掉"，纵轴让团队"把这一单变成下一单的产品杠杆"。

> **"团队"是一个光谱，不是固定编制。** 最小形态就是 **1 个人 + N 个 agent**——一个 4C 全占的 FDE 独自编排一支 agent 舰队，单人即整队；往上是 **多人 + 多 agent**——几个互补的人各自带一队 agent 协作。衡量单位不是人头，而是"**人类判断核心 × agent 舰队**"。下面所有角色，既可以由不同的人分担，也可以由同一个人在不同阶段切换戴不同的帽子，由 agent 补齐其余产能。

---

# 🤖 第一部分：团队的组成（人 + agent 舰队）

## 1. 人的核心角色（保持精简，只占 4C 里别人补不上的那一面）

下面是 AI-native FDE 团队涉及的核心角色。**注意：这是"角色"不是"人头"——小到 1 个人兼全部角色（其余产能交给 agent），大到每个角色配专人。**

| 角色 | 人负责什么（agent 补不上的） | 主要驻守阶段 |
|---|---|---|
| **FDE Lead** | 现场拆问题、对齐客户 CEO、端到端对结果负责 | 全程 |
| **Deployment Strategist** | 商业判断、关系与信任、把技术价值翻译成业务、scope 治理 | ①市场销售 / ④运维 |
| **FDSWE / Full-stack** | 系统架构、关键技术决策、review agent 产出 | ②③ 开发 |
| **Applied AI Engineer** | 模型选型、RAG/agent 设计、eval 标准、取舍 | ③ Demo |
| **Solution Architect / Tech Deployment Lead** | 生产架构、容量/安全/上线决策、跨团队推进 | ③b 生产级 |
| **CS / Adoption Owner** | 客户采用、关系维护、判断哪些需求该反哺产品 | ④ 运维 |

> 原型来自 Palantir 的 **Delta（快速原型工程师）/ Echo（业务对接 lead）** 模型。关键：**人只做判断、关系、架构、取舍这些"对结果负责"的事**，执行尽量交给 agent。

## 2. agent 舰队（过去要一个职能/团队，现在是 agent）

| Agent 角色 | 替代/放大的传统职能 | 跑在哪些工具底座上（见横轴） |
|---|---|---|
| **SDR / 获客 Agent** | 销售拓展、线索调研、外联 | CRM + Firecrawl + SalesGPT + 发信 |
| **Discovery Agent** | 需求收集、访谈记录、纪要整理 | 录音转写(FunASR/Meetily) + Spec Kit |
| **Design Agent** | 产品/UI 设计、原型、页面 | screenshot-to-code / Onlook / Penpot |
| **Coding Agent Fleet** | 前端/后端/算法工程师团队 | Claude Code / Codex / OpenHands fleet |
| **Data / RAG Agent** | 数据工程、文档处理 | Onyx/RAGFlow + Docling/MinerU + 连接器 |
| **Ops / SRE Agent** | 压测、IaC、部署、监控配置 | k6 + OpenTofu/Ansible + 监控栈 |
| **Support / CS Agent** | 一线客服、工单分流、采用引导 | Chatwoot Captain AI + 知识库 |

## 3. 团队配置：从 1 人到多人的光谱

人类核心可以小到 1 人、大到全角色小队，agent 舰队始终承担执行主体。两个维度共同决定配置：**客户规模**（决定要不要更多人审/治理）和**团队成熟度**（决定人 vs agent 的比例）。

| 形态 | 人类核心 | agent 舰队 | 适配客户 / 客户侧对接 |
|---|---|---|---|
| **单兵（1 人 + N agents）** | 1 个 4C 全占的 FDE，一人兼全部角色 | 重度依赖：SDR/discovery/coding/ops/support 全交给 agent | SMB / 早期项目；直接对客户 CEO |
| **小队（2-5 人 + 多 agent）** | 几个互补的人各带一队 agent | agents 承担执行主体，人做判断/架构/关系 | 中型客户；Sponsor + Process Owner + IT/数据对接 |
| **全队（全角色 + 多 agent + 人审）** | 全角色小队 + 安全/数据/PM | agents + 人审节点（合规要求高的环节） | Enterprise；RACI + 指导委员会（见后文客户角色规划） |

> 关键：**从单兵到全队是连续可伸缩的**——同一支团队可以在小客户上以"1 人 + agents"交付，在大客户上临时拉更多人结队，agent 舰队和产品化底座（纵轴）在所有形态下复用不变。

## 4. 现实标定（截至 2026-06）：一个人到底能编排多少 agent

> 数据来自 METR、Anthropic/OpenAI 工程博客及一线实践者，区分了"已确认"与"趋势叙事"。**结论：工具层面"1 人 + agent 舰队"已成立，但舰队规模受限于人的 review 带宽，不是 agent 供给。**

| 编排形态 | 现实规模（2026-06） | 工具支撑 |
|---|---|---|
| **主动监督**（你在实时 review 的） | **3–5 个甜区，上限约 10 个**（实践者共识：3 个专注常胜过 5 个分散） | Claude Code / Codex / Cursor 3.2 / Copilot |
| **异步过夜**（派活→收 PR，早上 review） | **几十个**（Jules 15→60 并发、Devin 企业版不限、Copilot/Codex Web 后台队列） | Jules / Devin / Copilot Coding Agent |
| **单任务内 fan-out**（一个任务的并行算力） | **上百 subagent**（Claude Code Dynamic Workflows，token 近似线性翻倍） | Claude Code Dynamic Workflows |

**单 agent 自主性**：METR 实测，50% 可靠度下前沿模型能独立完成的编码任务长度已达**十几小时量级**（Opus 4.6，2026-02），翻倍周期约 7 个月——**过夜整仓重构可行，但合并仍需人批**。

**⚠️ 诚实的边界（这恰恰证明"小人类核心"的价值）**：
- **瓶颈是验证不是生成**（Addy Osmani）。一个 FDE 的有效编排上限，由 ta 能可信审查多少产出决定。FDE 的杠杆点因此从"写码"转向"写好 plan/AGENTS.md、定 rubric、设自动检查、控 WIP"。
- **能力跑在可靠性前面**。"一个 90% 成功、在剩下 10% 不可预测地失败的 agent，是有用的助手，却是不可接受的自主系统"——长链路误差复利（每步 85%，10 步只剩 ~20%），高后果决策、客户关系、脏数据脏接口整合仍必须人主导。
- **AI 公司自己用的就是"FDE（人）+ agent 舰队"，不是纯舰队**：OpenAI 花 40 亿+收购咨询公司带入约 150 名 FDE；Anthropic 派 Applied AI/FDE 下场与客户共建；多位 CIO 直言"**FDE（稀缺的人）正成为 AI 落地的新瓶颈/限制因素**"。
- 所以"**1 人 + N agent**"在**单一、可验证、人在环抽检**的场景（编码/研究/内容/初期交付）放大 3–10 倍是真实的；在**多客户、跨遗留系统、高可靠、强客户关系的全自主交付**上还不成立——这正是为什么是"小人类核心 + 舰队"，而不是"无人舰队"。

---

# 🧭 第二部分：AI-native 三原则（团队级）

团队本身必须是 AI Native 的，否则就是"换了 AI 主题的传统乙方"：

1. **工具与模型**：团队带着最好的 agentic 编码工具（Claude Code / Codex）+ 最强模型进现场——这是 agent 舰队的能力上限，直接决定一个小团队能顶多少人。
2. **需求反哺**：团队把现场收集的真实需求和打磨好的 demo，**反哺回自家产品**（纵轴产品化底座），让一线信号变成产品迭代——这是从"做项目"到"做产品"的飞轮。
3. **团队投入**：FDE 团队花 **50% 的利润打造自有产品和品牌**——这是从"服务公司"升级为"产品公司"的分水岭，也是团队不被客户数拖垮的根本。

## 团队随身 AI 编码工具（agent 舰队的核心 · 2026-06 现状）

**商用旗舰（带进现场、配最强模型，关键看"能否一人并行多 agent"）**

| 工具 | 2026-06 形态 | 并行/舰队能力 |
|---|---|---|
| ⭐ **Claude Code** | Anthropic，跑 Opus 4.8；**Dynamic Workflows** 单会话可 fan-out 几十–上百 subagent | 单会话内大规模并行 + Managed Agents 托管调度 |
| **OpenAI Codex**（CLI/cloud） | 跑 GPT-5.5，**Terminal-Bench 2.1 ~83% 居首**；云沙箱后台并行多任务 | 云端并行 + subagent |
| **Cursor 3.2** | `/multitask` 异步派生 subagent + worktrees（报道 ~8 agent 并行） | 本地+云并行编排 |
| **GitHub Copilot** | 桌面 app（2026-06 GA），"My Work"统一面板，每会话独立 git worktree | 云端后台并行 + 控制台 |
| **Google Antigravity + Jules** | Antigravity 平台（Gemini CLI 已于 2026-06-18 并入）；**Jules 异步云 agent 15→60 并发** | 纯异步高并发 |
| **Devin**（原 Windsurf，Cognition） | 自主 agent + 指挥台；Pro 10 并发 / 企业版不限 | 纯异步"派活-收 PR" |

**开源/可私有化等价（客户要内网/air-gapped 时换上）**：⭐ OpenHands(79k·✅MIT,自托管沙箱) · Cline(64k·✅) · Aider(47k·✅) · Continue(35k·✅) · Goose(51k·✅) · Tabby(34k·✅,自托管补全) · 🇨🇳 Qwen Code(✅Apache,原生本地模型)。

> AI-native 的关键：编码 agent 不是"某个工程师的辅助"，而是**团队部署的一支可并行的工程舰队**——一个 FDSWE 同时 review 多个 agent 的产出。**2026 共识：脚手架（plan/rubric/hooks/WIP 控制）带来的差异，比换哪个前沿模型更大。**

---

# 🔧 第三部分：横轴 —— 团队如何覆盖客户全生命周期

每个阶段标注：**谁 own（人）· 人做什么 / agent 做什么 · agent 跑的工具底座**。

## 阶段 ① 市场与销售
**团队分工**：Deployment Strategist **own**。**人**：建立关系与信任、判断客户值不值得做、scope 把关。**Agent**：SDR agent 挖线索/调研公司/个性化外联/追踪提案信号/自动排期。
> ⚠️ 现状：销售/CPQ/Proposal 是开源生态**最薄弱**的一类，没有成熟成品 —— 团队要靠"CRM + 抓取 + LLM + 发信"自己拼一个 AI SDR。

| 工具类型 | 开源项目（star · 许可） |
|---|---|
| CRM / 客户关系 | ⭐ Twenty(52k·⚠️AGPL,为AI设计,agent易读写) · Atomic CRM(1.1k·✅MIT,自建脚手架) · Krayin(23k·✅MIT) · ⚠️ Odoo(53k·LGPL,含CPQ) · ⚠️ ERPNext(36k·GPL,带报价) |
| 营销 / 获客 / 发信 | ⚠️ Mautic(10k·GPL) · ⚠️ Listmonk(22k·AGPL) · Postal(17k·✅MIT,自建发信) · Dittofeed(3k·✅MIT) |
| 建联 / 约 demo | ⭐ Chatwoot(34k·✅MIT,全渠道+Captain AI) · ⚠️ Cal.com(46k·AGPL)｜MIT 分支 cal.diy |
| 提案追踪 / 电签 | ⚠️ Papermark(8k·AGPL,逐页追踪) · ⭐ Documenso(14k·⚠️AGPL) · DocuSeal(17k·⚠️AGPL,API最干净) |
| AI SDR（自建） | SalesGPT(3k·✅MIT,销售agent) · open-sdr(MCP,公司调研) |

> **团队的 AI SDR 配方**：Twenty(CRM) + Firecrawl(调研富集) + Claude/Gemini(LLM) + Postal(发信) + SalesGPT(对话) → 一个 Deployment Strategist 编排这套 agent，顶过去一整个 SDR 团队。

## 阶段 ② 需求与设计
**团队分工**：FDE Lead + Applied AI Engineer **own**。**人**：现场 discovery、判断真需求、和客户 CEO 对齐目标、产品判断。**Agent**：discovery agent 录音→转写→结构化需求卡片；从纪要生成 spec/issue；design agent 从描述/截图生成可点击原型。

| 工具类型 | 开源项目（star · 许可） |
|---|---|
| 现场 discovery 捕获 | ⭐ whisper.cpp(51k·✅) · WhisperX(23k·✅,词级+分离) · Meetily(13k·✅,本地全链路) ｜ 🇨🇳 ⭐ FunASR(19k·✅,中文ASR标杆) |
| PM / 需求 / 项目管理 | ⭐ Plane(54k·⚠️AGPL,+AI) · OpenProject(15k·✅GPL) · Huly(26k·✅EPL) |
| 需求结构化 / 规格 | ⭐ GitHub Spec Kit(111k·✅MIT,Spec→Plan→Tasks) · OpenSpec(58k·✅MIT) |
| 图 / 白板 / 流程 | ⭐ Excalidraw(90k·✅) · Mermaid(89k·✅) · ⚠️ bpmn-js(自有,BPMN标准) |
| 产品/UI 设计 / 原型 | ⭐ Penpot(55k·✅MPL,Figma最佳替代) · ⚠️ tldraw(45k·源可见,Make Real) |
| AI 生成 UI / 页面 | ⭐ screenshot-to-code(72k·✅MIT) · Onlook(26k·✅Apache,改真React代码) · OpenUI(22k·✅) · Dyad(15k·✅,本地私有) |
| 设计系统 | shadcn/ui(104k·✅) · 🇨🇳 Ant Design(99k·✅,中后台) |
| 知识图谱 / 本体 | Graphiti(20k·✅,时序知识图) · LinkML(0.5k·✅) |

## 阶段 ③ 开发与测试
分两步：先 **(a) Demo** 验证价值，再 **(b) 生产级** 扛真实负载。

### ③a Demo 过程
**团队分工**：FDSWE + Applied AI Engineer **own**。**人**：架构、关键技术决策、review agent 产出、定工程化标准。**Agent**：coding agent fleet 并行写前后端/算法、data agent 接客户数据做 RAG、自动跑 eval。

| 工具类型 | 开源项目（star · 许可） |
|---|---|
| AI 编码 agent | 见上「团队随身 AI 编码工具」（OpenHands/Cline/Aider…）|
| Agent 编排框架 | ⭐ LangGraph(36k·✅,有状态可审计) · Pydantic-AI(18k·✅,类型安全) · CrewAI(55k·✅) · Agno(41k·✅,带控制面) |
| RAG / 数据接入 | ⭐ Onyx(31k·✅,带权限RAG) · LlamaIndex(50k·✅) · Airbyte(22k·✅,600+连接器) ｜ 🇨🇳 ⭐ RAGFlow(84k·✅) · ⚠️ Dify(147k,私部署OK) |
| 文档解析 / OCR | ⭐ Docling(62k·✅) · MarkItDown(162k·✅) ｜ 🇨🇳 ⭐ MinerU(72k·⚠️,中文PDF最强) · PaddleOCR(84k·✅) |
| 向量库 | ⭐ pgvector(22k·✅,复用客户PG) · Qdrant(33k·✅) · Milvus(45k·✅) |
| 浏览器/computer-use | ⭐ browser-use(102k·✅,操作无API老系统) · ⚠️ Skyvern(22k·AGPL) |
| 评估 / 工程化标准 | ⭐ promptfoo(23k·✅,CLI+红队) · DeepEval(17k·✅) · Ragas(15k·✅) |
| 可观测 / 护栏 | ⭐ Langfuse(30k·✅) · Opik(20k·✅) · Presidio(10k·✅,PII脱敏) |

### ③b 生产级过程
**团队分工**：Solution Architect / Tech Deployment Lead **own**。**人**：生产架构、容量规划、安全、上线决策。**Agent**：ops agent 生成 IaC、写压测脚本、配监控、自动化部署。

| 工具类型 | 开源项目（star · 许可） |
|---|---|
| 压测 / 并发 | ⭐ k6(31k·⚠️AGPL,JS脚本) · Locust(28k·✅MIT) · Vegeta(25k·✅MIT) · JMeter(9k·✅) |
| 数据库 | ⭐ PostgreSQL(✅) · ClickHouse(48k·✅,OLAP) · Valkey(26k·✅,Redis替代) ｜ 🇨🇳 TiDB(40k·✅) · openGauss(✅信创) · ⚠️ OceanBase(10k·木兰) |
| 基础设施即代码 IaC | ⭐ OpenTofu(29k·✅MPL) · Pulumi(25k·✅) · ⭐ Ansible(69k·✅GPL,纯SSH内网神器) |
| 容器 / 编排 | ⭐ k3s(33k·✅,轻量K8s内网首选) · Kubernetes(123k·✅) · ⭐ Docker Compose(38k·✅,单机一键全栈) |
| CI/CD | ⭐ Gitea+Actions(57k·✅MIT,内网一体机) · Woodpecker(7k·✅) · ArgoCD(23k·✅,GitOps) |
| 基础设施监控 | ⭐ Prometheus(65k·✅)+Grafana(75k·⚠️AGPL) · SigNoz(28k·✅) · ⭐ Uptime Kuma(89k·✅,拨测看板) |

## 阶段 ④ 迭代与运维
**团队分工**：CS / Adoption Owner **own**。**人**：客户关系、推动采用、判断哪些需求该反哺产品。**Agent**：support agent 一线分流(Captain AI)、自动收反馈、监控告警、生成 runbook。

| 工具类型 | 开源项目（star · 许可） |
|---|---|
| 工单 / Helpdesk | ⭐ Chatwoot(34k·✅MIT,全渠道+Captain AI) · ⚠️ Zammad(6k·AGPL,正规SLA) · ⚠️ FreeScout(4k·AGPL) |
| 客户成功 / Onboarding | ⭐ Driver.js(26k·✅MIT,4KB引导库) · Usertour(2k·✅MIT) |
| 状态页 / 可用性 | ⭐ Uptime Kuma(89k·✅) · Gatus(11k·✅) · Cachet(15k·✅BSD) |
| 帮助中心 / 知识库 | Docusaurus(66k·✅) · BookStack(19k·✅,SOP/Runbook) |
| 反馈 / 需求变更 | ⚠️ Fider(4k·AGPL,投票排序) · ⚠️ Plane(54k·AGPL) |
| 采用度量 / 回流 | ⭐ PostHog(35k·✅,分析+实验+调研) · Umami(37k·✅) · ⚠️ OpenReplay(12k·ELv2,会话回放) |
| Prompt / 资产沉淀 | ⭐ Langfuse(30k·✅,prompt版本+eval) · Agenta(4k·✅) |

---

# 👥 第四部分：客户侧角色规划（团队开局就和 CEO 对齐）

> 这是 FDE **团队**与客户协作的接口——FDE 团队再 AI-native，也要先搞清楚客户方谁参与、做什么。开源没有强势的专用 RACI 工具（用 Markdown 模板 + Plane 自定义字段即可）。参考：[responsibility-assignment-matrix](https://github.com/joelparkerhenderson/responsibility-assignment-matrix)。

**核心原则**：kickoff 前就和客户 CEO/高管把"**谁参与、各自做什么、谁拍板**"一次性对齐，产出**一页 RACI + 一张干系人地图**，每个任务只能有一个 A。

**客户侧必备角色**：Executive Sponsor（出资拍板）· 业务负责人/Process Owner（定义成功）· 客户侧 PM（单点对接 SPOC）· SME 业务专家 · 数据 Owner（定义/质量/权限/合规）· IT/平台/安全对接人 · 终端用户代表/Super User（采纳与培训）· 变更管理负责人。

**干系人地图（Power/Interest）**：高权高兴趣=Key Players（CIO/VP，每周参与决策）｜高权低兴趣=Keep Satisfied（CEO/CFO，月度摘要）｜低权高兴趣=Keep Informed（分析师/Super User，周报）。

**随规模/行业变化**：SMB → FDE 团队直接对 CEO，客户侧 1-2 关键人即可，不搞重型治理；Enterprise → RACI + 指导委员会，配齐 Sponsor/Process Owner/数据治理/IT/安全/采购/法务 + 定期高管 Review；受监管行业（金融/医疗/政府）→ kickoff 即前置合规/安全/法务。**数据越敏感、监管越强，数据 Owner 与安全/法务越要前置。**

---

# 🏛️ 第五部分：纵轴 —— 团队的产品化飞轮（护城河）

这是**整个团队共享的资产/产品**，不是某个人的工具——每次客户交付的资产都沉淀于此，需求反哺于此，团队的 50% 利润投在这里。对应 Palantir 的 Foundry → Ontology → AIP。

| 层 | 开源项目（star · 许可） | 对应 Palantir | 团队怎么用它做产品化 |
|---|---|---|---|
| ① 数据集成/编排 | ⭐ Dagster(13k·✅,资产/血缘) · Airflow(38k·✅) · dbt-core(11k·✅) · Iceberg(8k·✅) · DuckDB(30k·✅) | Foundry | 把每次现场数据处理变成版本化、带血缘的**资产**，进团队资产库 |
| ② 语义/本体/治理 | ⭐ Cube(20k·✅,语义层) · ⭐ DataHub(11k·✅,血缘) · LinkML(0.5k·✅,本体) · Graphiti(20k·✅,知识图) | Ontology | 把客户业务口径/实体关系固化为团队可复用的**语义模型/本体** |
| ③ IDP/低代码 | ⭐ Backstage(29k·✅,内部产品货架) · Appsmith(40k·✅) · Refine(35k·✅) | IDP | 把交付物登记成团队"产品货架"、做成可复用 App 模板 |
| ④ BI/可视化 | Superset(70k·✅) · Evidence(6.5k·✅,BI as code) · Lightdash(5.7k·✅) | — | 标准化看板产品、报告即代码跨客户复用 |
| ⑤ 在数据上建AI应用 | ⭐ WrenAI(16k·✅,GenBI) · Vanna(22k·✅,text-to-SQL) · Superduper(5k·✅) | AIP | 语义模型+客户数据+Agent 一体，产品化成可复用 AI 应用 |

**「Foundry-lite」团队产品底座（全 ✅ 可商业交付）**：Dagster + dbt + Iceberg → Cube + LinkML/Graphiti → DataHub → Appsmith/Refine + WrenAI/Vanna。

---

# ⚙️ 第六部分：团队自身的 AI-native 运营底座

让**一个小团队 + agent 舰队同时服务多个客户**而不线性扩人——这是 AI-native FDE 团队区别于传统乙方的内部基础设施：

| 能力 | 用什么 | 团队级用法 |
|---|---|---|
| **多客户 agent 编排** | Agno(41k·✅,带控制面) / LangGraph(36k·✅) | 一租户=一客户，统一编排各客户的 agent 舰队，人审节点守生产 |
| **共享知识图谱** | Graphiti(20k·✅) / Cognee(26k·✅) | 跨客户的领域本体与现场知识沉淀，新项目可复用 |
| **Agent/Prompt 资产库** | Langfuse(30k·✅) | 现场打磨的 prompt/agent 配置经 eval 验证后晋升为团队复用资产 |
| **内部 IDP / 货架** | Backstage(29k·✅) | 团队的服务、连接器、模板、资产统一登记，新成员/新项目即取即用 |
| **统一 LLM 网关** | LiteLLM(52k·✅) ｜ 🇨🇳 one-api(35k·✅) | 团队统一接入模型、按客户/项目限流计费，内网可部署 |
| **权限 / 多租户隔离** | Casbin(20k·✅) · OpenFGA(5k·✅) | 团队成员/agent 对各客户资源的细粒度权限 |

---

# 🧠 团队的模型舰队：按场景选模型（2026-06）

> 给 agent 舰队配模型，按"贵但强 / 便宜跑量 / 内网开源"三档分工。**非 Claude 的型号/价格来自第三方榜单（截至 2026-06，会变），落地前务必用你们自己的 eval 复测。** Claude 价格为官方口径。

**① 联网客户：带最强 agent 模型进现场**
| 档 | 模型（输入/输出 $/M） | 说明 |
|---|---|---|
| 旗舰（最难的 agent 编码/关键决策） | Claude **Fable 5**($10/$50) / **Opus 4.8**($5/$25,可买到最强 Opus) · **GPT-5.5**($5/$30,Codex Terminal-Bench 居首) · **Gemini 3.1 Pro**($2/$12) | 现场最强编码 agent |
| 中端（日常 80% 工作流） | Claude **Sonnet 4.6**($3/$15) · **GPT-5.4**($2.50/$15) · **Gemini 3 Flash**($0.50/$3) | 性价比主力 |
| 便宜跑量（批处理/抽取/分类） | Claude **Haiku 4.5**($1/$5) · **GPT-5.4 Nano**($0.20/$1.25) · 🇨🇳 **DeepSeek V4-Flash**(~$0.14/$0.28) | 海量调用 |

**② 内网 / air-gapped / 信创：开放权重(可私有化部署)**
| 类型 | 模型（许可） | 说明 |
|---|---|---|
| 通用旗舰 | 🇨🇳 **Qwen3.x**(Apache,国产事实标准·尺寸最全) · **DeepSeek V4**(MIT,许可最干净) | 内网默认底座 |
| 顶尖编码（离线） | 🇨🇳 **DeepSeek V4-Pro**(MIT,LiveCodeBench 居前) · Qwen Coder · **GLM-5.2**(开放权重) | air-gapped 也拿到近前沿编码 |
| 长上下文/多模态 | 🇨🇳 **Kimi K2.x**(开放,长文档) · **MiniMax M3**(开放,原生多模态+1M) · Qwen-VL | 内网唯一兼顾多模态 |
| 端侧/低算力 | 🇨🇳 **MiniCPM**(无 GPU 现场,CPU/手机端) · **Mistral Large 3**(Apache,多语言) | 边缘部署 |
| 推理部署 | 🇨🇳 ⭐ **Xinference**(✅,私有化最省心) · **LMDeploy**(✅,信创/昇腾) · **vLLM**(✅,通用) | 国产算力/内网 |

> ⚠️ 闭源仅 API（**不能进 air-gapped 客户**）：Claude 全系、GPT 全系、Gemini 全系、Qwen-Max 档。进内网客户必须备一套开放权重（DeepSeek MIT / Qwen Apache 是许可最干净的两条路）。
> 💡 Computer-use 按工作面路由：**浏览器→Gemini**、**桌面→Codex/Claude**；内网多模态用 **MiniMax M3**。

**FDE 模型路由速记**：联网最强 → Opus 4.8 / GPT-5.5(Codex) / Gemini 3.1 Pro；便宜跑量 → Haiku 4.5 / DeepSeek V4-Flash；air-gapped 兜底 → DeepSeek V4(MIT) + Qwen3.x(Apache)。**脚手架比模型更决定成败。**

---

# 🖥️ AI 硬件：随身 / 现场部署 / 边缘 / 捕获（2026-06）

> 模型选完还要落到**硬件**：FDE 既要带设备进现场，又要在客户（尤其 air-gapped/信创）落地推理硬件。**型号/价格截至 2026-06、变化快、采购前按当周报价复核**；标 🟡 = 路线图/未全面铺货。**主线和模型一致：联网=NVIDIA+闭源模型；中国 air-gapped/信创=国产芯片/一体机+开源权重。**

## ① 随身设备（FDE 带进现场跑本地 agent/模型，隐私敏感数据不出机）
| 设备 | 价格 | 跑 70B | 适合 |
|---|---|---|---|
| ⭐ **MacBook Pro M5 Max 128GB** | ~$4,500+ | ✅ 12–25 tok/s，全天续航 | 最便携全能，背包里的 70B 工作站 |
| **NVIDIA DGX Spark**（GB10，128GB） | ~$4,699 | ⚠️ ~2.7 tok/s（带宽瓶颈） | 本地微调 + CUDA 生态对齐（非纯推理） |
| **AMD Strix Halo 迷你主机**（128GB） | $1,499–2,500 | ✅ 可跑 +120B | 最便宜的本地 128GB 离线盒子 |
| 🟡 **NVIDIA RTX Spark 笔记本**（GB10，128GB） | 未定（2026 秋） | 待测 | 观望：GB10 算力笔记本化 |

## ② 现场推理部署（在客户机房/数据中心落地大模型）
**联网客户（NVIDIA）**
| 硬件 | 显存 | 能跑 | 注意 |
|---|---|---|---|
| ⭐ **H200** | 141GB | 单卡 70B FP16，生态最稳 | 买得到、最稳的一档 |
| **B200 / B300** | 192GB / 288GB | 70B–百亿级长上下文 | ⚠️ **B300/GB300 强制液冷**，机房没液冷上不了 |
| **GB200 / GB300 NVL72** | 整柜 | **671B/万亿实时推理** | 液冷整柜，机房改造大 |
| **RTX PRO 6000 Blackwell** | 96GB | 单卡 70B FP8（PoC 单机最佳） | "今天就让客户看到效果" |

**air-gapped / 信创（中国主流 · DeepSeek 671B 私有化标准答案）**
| 路线 | 代表 | 关键 |
|---|---|---|
| ⭐ **大模型一体机**（开箱即用） | 华为 **Atlas 800I A2** / 浪潮 / 新华三 / 联想（昇腾/海光底） | 671B：昇腾 **16 卡(W8A8) / 32 卡(BF16)**；厂商打包 OS+CANN+vLLM+模型，FDE 工作量降到"配业务+接数据" |
| **国产芯片自组栈** | 🇨🇳 昇腾 **910B/910C**(+CANN+vLLM-Ascend) · **950PR**(国内唯一 FP4,🟡2026) · **海光 DCU**(x86 兼容,迁移省事) · **寒武纪思元590** | DeepSeek 爆火后 16 家国产芯片已 Day-0 适配 |

> ⚠️ 三个必查坑：① **昇腾 910B 不支持 FP8**（DeepSeek FP8 权重要转 BF16，体积 ~640GB→~1.3TB，按 BF16 算显存）；② **B300/GB300 强制液冷**；③ **信创清单**决定能不能用 NVIDIA（高端卡对华出口受限）。

## ③ 边缘 / 端侧（客户现场留一个低功耗离线推理节点）
🇨🇳/全球：**Jetson Orin Nano Super**($249,≤8B,最便宜边缘生成式) · **Jetson Thor**(128GB,机器人/大模型级) · **Hailo-8 M.2**(26 TOPS,插进现有工业 PC 加挂) · 国产边缘盒子 🇨🇳 **后摩 M50 / 爱芯元智 / Thundercomm**（国密合规、纯端侧）。

## ④ 现场捕获硬件（对应 discovery 录音）⚠️ 隐私是雷区
| 设备 | 价格 | 隐私 | FDE 用法 |
|---|---|---|---|
| **Plaud NotePin S / Note Pro** | $159–189 | ✅ 可开**完全本地模式**（音频不上云） | 通用现场访谈捕获，敏感客户务必开本地模式 |
| ⭐ **Omi**（开源 MIT） | ~$89 | ✅ **完全自托管，数据 100% 本地** | 客户要求"音频绝不出本地"时唯一选择，可接自有模型 |
| 🇨🇳 **讯飞 S8 离线版** | — | ✅ **国密二级 + 离线转写** | 中国政企/政府敏感访谈合规首选 |
| ❌ Limitless（Meta 收购停售）/ Bee（强依赖 Amazon 云） | — | ⚠️ 不可控 | **不建议用于客户敏感现场** |

## ⑤ FDE 现场部署"按场景选硬件"
| 场景 | 推荐 | 备注 |
|---|---|---|
| 联网客户、要快/弹性 | 云 GPU（H200/B200，AWS/GCP/国内云） | 不买硬件、按小时付费；B200 供给紧 |
| 联网、自建推理服务 | 自购 H200（最稳）或 B200/B300 | B300 需液冷 |
| **air-gapped 信创（主流）** | **大模型一体机**（Atlas 800I A2 跑 DeepSeek 671B） | 数据不出域+开箱即用+国产合规 |
| 单机 PoC / 现场 demo | **RTX PRO 6000 96GB**（敏感客户换国产单机/小一体机） | 单卡 70B，最快出效果 |
| FDE 随身 | **MacBook Pro M5 Max 128GB**（+ 需微调加 DGX Spark） | 背包里的 70B 工作站 |
| 顶配训练/微调 | GB200/GB300 NVL72；信创走昇腾 Atlas 950 超节点 | 整柜液冷、机房改造大 |

---

# ⚠️ 许可证避雷（对外交付/闭源分发前必看）

团队对客户做闭源或 SaaS 交付时需法务评估：
- **AGPL-3.0**：Twenty、Cal.com、Documenso、DocuSeal、Papermark、Listmonk、Plane、k6、Grafana、Loki、Zammad、FreeScout、Fider、Skyvern、Firecrawl、new-api、QAnything、ToolJet、Metabase、Permify 等。
- **GPL-3.0**：Mautic、ERPNext、OpenProject、Netdata、MaxKB、Budibase 等。
- **BSL/ELv2/SSPL/源可见/自有**：Vault & Nomad & 旧 Terraform(BSL)、Redis(SSPL)、Outline(BSL)、tldraw、Dify、FastGPT、MinerU、MindsDB(ELv2)、OpenReplay(ELv2)、OceanBase(木兰)。

**规避技巧**：CRM 用 Atomic CRM/Krayin(MIT)、约会议用 cal.diy(MIT)、Terraform 用 OpenTofu(MPL)、Redis 用 Valkey(BSD)。**最安全**：所有标 ✅ 的 MIT/Apache/BSD/MPL/PostgreSQL 项目。

---

# 🎯 团队起步配置（每阶段一件 ⭐，1 人 + agents 即可起步，多人结队同栈复用）

> "谁 own"列是角色不是人头：单兵形态下这些角色由同一个 FDE 在不同阶段切换戴帽，agent 舰队补齐执行；多人形态下分给不同的人。**工具底座两种形态完全一致。**

| 阶段 / 维度 | 谁 own | 国际首选 | 🇨🇳 中文/信创 |
|---|---|---|---|
| 随身 AI 工具 | 全员 | Claude Code / Codex（内网→OpenHands fleet）| Qwen Code |
| ① 市场销售 | Deployment Strategist | Twenty + Chatwoot + Documenso + SalesGPT | （同左）|
| ② 需求设计 | FDE Lead + Applied AI | Spec Kit + Plane + Penpot + Onlook | FunASR + Ant Design |
| ③a Demo | FDSWE + Applied AI | OpenHands fleet + Onyx + promptfoo + Langfuse | RAGFlow + MinerU |
| ③b 生产级 | Solution Architect | k3s + PostgreSQL + k6 + Prometheus/Grafana + Gitea | TiDB/openGauss + Xinference |
| ④ 迭代运维 | CS / Adoption Owner | Chatwoot + Uptime Kuma + Plane/Fider + PostHog | — |
| 产品化飞轮 | 全团队 + 产品 | Dagster + dbt + Cube + WrenAI | （模型换国产）|
| 团队运营底座 | FDE Lead | Agno + Langfuse + Backstage + LiteLLM | one-api |
| 模型舰队 | Applied AI | 联网→Opus 4.8/GPT-5.5/Gemini 3.1 Pro；跑量→Haiku 4.5/DeepSeek V4-Flash | air-gapped→DeepSeek V4(MIT)+Qwen3.x(Apache) |
| AI 硬件 | Solution Architect | 随身 MacBook M5 Max 128GB；联网部署 H200/B200 | 现场 PoC RTX PRO 6000；air-gapped 大模型一体机（Atlas 800I A2）；捕获 Plaud 本地模式/讯飞离线 |

---

*本文件以「AI-native FDE 团队」为视角：小人类核心 + agent 舰队，覆盖客户全生命周期（市场→签约→设计→开发→上线→运维）× 产品化飞轮（纵轴）× 团队运营底座 × 客户角色规划 × 模型舰队 + AI 硬件（2026-06 现状），约 160+ 个开源项目 + 主流模型/硬件选型，带 star + 许可证标记 + ⭐必备 + 团队角色归属。可作为 OpenFDE 组建/运营 AI-native FDE 团队与自建工具的选型基线。*
