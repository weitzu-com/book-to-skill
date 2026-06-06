---
name: book-to-skill
description: |
  书道（book-to-skill）——把一本书转化成一个可复用的 Claude Code Skill 的流水线。
  当用户说「把这本书做成 skill / 技能」「book to skill」「把这本 PDF/电子书提炼成 skill」
  「读完这本书帮我封装成能力」「把某某方法论做成可调用的 skill」，或给出一本书
  （PDF / 扫描版 PDF / EPUB / Markdown / TXT）并希望沉淀为可长期复用的 Claude 能力时，使用本 skill。
  覆盖：格式预处理（含扫描版 OCR）、多 Agent 并行深度解析、认知架构设计、SKILL.md 编写、
  references 六件套、五维验证、Workflow 并行。经五轮真实书籍（135–314 页，MD/PDF文本/PDF扫描）验证。
license: MIT
metadata:
  version: v2.5
  author: 原点知识库 / 书道流水线
  validated_on: 5 books (会计七原则 / Joe Girard / Claude Code手册 / 经营十二条 / Harness工程之道)
  changelog: "v2.4 新增溯源门禁（要素须可溯源、不编造原书没有的内容）；v2.5 新增发布可见性门禁（他人著作=private）+ 同源去重（防并发孤岛）+ 锚点闭环核查"
---

# 书道 · book-to-skill

> **一句话**：书道是一条把「一本书」编译成「一个 Skill」的流水线。
> 输入一本书 → 输出一个带 SKILL.md + references 六件套 + scripts 的、可被 Claude Code 调用的能力。
>
> **第一性原理**：一本书的价值 = 它改变读者「如何判断与行动」的能力。
> 把书做成 skill，不是把书"存起来"，而是把书的**判断力**提炼成 Claude 可随时调用的判断力。
> 因此：**不以"记住了多少"为验收，以"能否在新场景里做出符合原书精神的判断"为验收。**

---

## 何时使用 / 不适用

**使用**：用户想把一本书（或一套方法论、一份长文档）转化为可长期复用的 Claude Code Skill。

**不适用**（明确说"不"）：
- 只是想"读一遍/总结这本书" → 直接读，不必建 skill。
- 一次性问答、不需要沉淀 → 不必建 skill。
- 源材料 < 1 章 / 信息密度过低 → 价值不足以封装。
- 纯虚构小说 / 无可迁移方法论 → 书道提炼的是"判断与行动模式"，无此则不适用。

---

## 七阶段流水线总览

```
阶段零  预处理决策     判格式 + 冲突检测（先判断，再动手）
阶段一  结构化         → book_structured.md（章节边界 + 全角→半角）
阶段二  深度解析       多 Agent 并行，四层提取：概念→框架→方法→原则
阶段三  认知架构设计   五要素：身份/知识分配/能力边界/行为模式/交互协议
阶段四  Skill 编写     SKILL.md（<500行）+ references 六件套 + scripts
阶段五  五维验证       覆盖度/关系/应用/判断/边界——以"用"为验，不以"记"为验
阶段六  归档闭环       知识图谱 + 工作日志 + 索引（原点 KB）
```

**每阶段完成标准（checkbox，解决"什么时候算做完"）**：见 `references/00-pipeline.md`。
**每阶段失败模式 + 应对**（"做完但做错了怎么办"）：见 `references/00-pipeline.md`。

---

## 阶段零：预处理决策树（入口判断，必走）

```
源文件是什么格式？
├── MD（已优化）       → 跳过预处理，查目录完整性          ~2min
├── MD（未优化）       → 全角→半角 + 层级规范化            ~5min
├── PDF（文本型）      → scripts/pdf_to_text.sh → 结构化   ~10-15min
└── PDF（扫描型/OCR）  → ⚠️ 文件名标(OCR)≠Read能读文字
                        方案A 首选：scripts/extract_pdf.py（PyMuPDF 提嵌入OCR层，258页<30s）
                        方案B：tesseract chi_sim OCR（无文字层时）
                        门禁：关键语义段可读率 ≥60% 才进阶段二，否则重扫
```

**冲突检测（动手前必做，查"同名"更要查"同源"·v2.5）**：
1. **同名/近似**：搜索 `~/.claude/skills/` 是否有同名 skill。
2. **同源（防并发孤岛）**：以「书名 / 作者 / 中文全名」为关键词，跨这几处搜是否已被别处建过——`~/.claude/skills/`（含中文名目录）、私有备份仓（如 `claude-skills`，用 `gh api repos/<owner>/<repo>/contents`）、原点工作日志（`工作日志/*<书名/书道>*`）。⚠️ 同源 skill 常以**中文书名**落在**私有仓**，只查标准路径必漏。
3. 命中 → 问用户「更新 / 新建 / 取消」；已存在且质量高 → **仅补路由加载指令**（不推翻），合并取"信息量大者为 base + 嫁接对方独有"。
4. 不存在 → 创建新 skill。

> 详细格式处理、扫描版 OCR 专项、章节边界检测 → 读 `references/01-preprocess.md`。

---

## 阶段二：多 Agent 并行深度解析

**Agent 数量决策表**：

| 章节数 | Agent 数 | 分配策略 | 预计 |
|--------|---------|---------|------|
| <8 | 1 | 单人全量 | 5-10min |
| 8-15 | 2 | 前半 + 后半 | 10-15min |
| 15-25 | 3 | 核心章 + 后期章 + 中间补全 | 15-25min |
| 25+ | 4+ / Workflow | 按主题分组 | 20-35min |

**四层提取（提取维度）**：概念(L1) → 框架(L2) → 方法(L3) → 原则(L4)。
**案例不是独立层**，而是每个知识要素的「验证锚点」（必须标注书中出处）。

**亲自交叉验证（不可跳过）**：选 2-3 个最知名核心章亲自读，对照 Agent 输出查漏补缺。

**🔒 溯源门禁（v2.4，不可跳过）**：L1–L4 每个要素必须能溯源到书中真实位置（章节/页码/原文片段）。**溯源不到的标 `[待核]`，绝不编造原书没有的框架、金句或数据**——book→skill 最大失败模式是"自信地虚构作者没说过的话"。宁可少一条真知识，不可多一条假知识。

> Agent prompt 模板、三 Agent 标准分工、隐含假设与矛盾调和 → 读 `references/02-parse.md`。
> 章节 ≥9 用 Workflow 并行（pipeline 先到先出）→ 读 `references/05-workflow.md`。

---

## 阶段三/四：认知架构 + Skill 编写

**认知架构五要素**（设计前先答这五问）：

| 要素 | 关键问题 |
|------|---------|
| 身份定位 | 这个 skill 以谁的身份说话？（实操者→以作者身份；学者→以"讲解人"身份）|
| 知识分配 | 什么放 SKILL.md，什么放 references/？ |
| 能力边界 | 什么能做、什么不能做？ |
| 行为模式 | 用户问什么 → skill 回什么？ |
| 交互协议 | 用什么命令/路由触发？ |

**SKILL.md 铁律**：YAML frontmatter 用 block scalar `|`；**总行数 < 500**；含 references 检索提示；含命令参考表。

**references 六件套**（缺一不可）：
```
concepts.md         L1 概念 + 出处 + 锚点
frameworks.md       L2 框架 + 章节对照
methods.md          L3 方法 + 步骤 + 输入输出 + 验证标准
principles.md       L4 原则 + 边界条件 + 矛盾调和
cases.md            10 个关键案例 + 可测试问题
knowledge_graph.md  知识图谱 + 完整度热图 + 隐含假设
```

**路由加载指令（v2.0 核心创新，必做）**：SKILL.md 路由表每条都要附**具体加载指令**，格式
`方法→references/methods.md#方法N`。**"写了但调不到" = 知识不存在。**

> 认知架构展开、SKILL.md 模板、六件套写法 → 读 `references/03-authoring.md`，模板见 `templates/`。

---

## 阶段五：五维验证（以"用"为验）

| 维度 | 方法 | 标准 |
|------|------|------|
| 概念完整 | 抽 20 个概念查覆盖 | 100% |
| 关系完整 | 知识图谱无孤立节点 | 0 孤立 |
| 应用正确 | 10 个案例角色扮演 | 核心判断一致 |
| 判断准确 | 5 个变体场景 | 推理符合原书精神 |
| 边界清晰 | 3 个边界场景 | 正确说"不" |

**🔒 溯源抽检（v2.4）**：随机抽 5 个 L1–L4 要素，逐条回原书核对出处真实存在；命中 `[待核]` 或查无实据者，删除或补源后才算通过。这是「应用正确/判断准确」的前置——**虚构的知识再"自洽"也是污染**。

**结构验证可自动化**：`python3 scripts/check_skill.py <skill_dir>`（查行数/概念数/孤立节点/六件套齐全/路由加载指令）。

**🔒 锚点闭环核查（v2.5，不可跳过）**：扫描所有 `references/*.md#anchor` 引用，逐条确认目标文件有对应 `<a id>` 定义；任一引用无锚点 = 死链 = "写了调不到=知识不存在"，补 `<a id>` 或删引用后才算通过。**工具绿灯（check_skill 通过）≠ 真过**，此核查工具未覆盖、须单独跑。

> 五维判据 + 防错清单 → 读 `references/04-validation.md`。

---

## 阶段六：归档闭环 + 🔒 发布可见性门禁（涉对外动作必走，v2.5）

知识图谱 + 工作日志 + 索引（原点 KB）。**凡涉 GitHub / 任何对外发布，先过版权判定，再定可见性——这是不可逆动作，错了就是"已公开过"。**

**版权 → 可见性 决策（推送前强制自答）**：

| 产出来源 | 可见性 | 理由 |
|---|---|---|
| 自有方法论 / 自创框架（如书道本身）| 可 public | 无第三方著作权 |
| 他人著作提炼（书的概念/框架/原文片段/数据）| **必须 private** | skill 内含受版权内容，public = 侵权暴露 |
| 拿不准 | **默认 private** | 撤回成本 >> 改公开成本 |

**铁律**：用户说"public"≠ 免除判断。源是他人著作 → **先告知版权风险、建议 private，再执行**；已含书籍提炼内容的 skill **默认 private**。README 须带"仅供参考、非法律意见、知识有时效"免责声明。改可见性：`gh repo edit OWNER/REPO --visibility private --accept-visibility-change-consequences`。

---

## 命令 / 脚本参考

| 用途 | 命令 |
|------|------|
| PDF 文本型 → TXT（保版式+全角转半角）| `bash scripts/pdf_to_text.sh book.pdf` |
| 扫描版 PDF 提取嵌入 OCR 文字层 | `python3 scripts/extract_pdf.py book.pdf > full_text.txt` |
| 从 TXT 检测章节边界 → 结构化骨架 | `python3 scripts/detect_structure.py full_text.txt` |
| 对产出 skill 做五维结构验证 | `python3 scripts/check_skill.py <skill_dir>` |

---

## references 加载路由表（按需检索，省 token）

| 你需要… | 读这个 |
|---------|--------|
| 七阶段完成标准 + 失败模式 | `references/00-pipeline.md` |
| 格式判断 / 扫描版 OCR / 章节边界 | `references/01-preprocess.md` |
| 阶段二 Agent prompt + 分工 + 四层提取 | `references/02-parse.md` |
| 认知架构五要素 + SKILL 写法 + 六件套 | `references/03-authoring.md` |
| 五维验证判据 + 防错清单 | `references/04-validation.md` |
| Workflow 并行脚本 + 效率基准 | `references/05-workflow.md` |
| 三省六部治理 + 中华经典三层治理 | `references/06-governance.md` |
| 产出 skill 的骨架模板 | `templates/` |

---

## 中华经典三层治理（书道的方法论根）

- **谋（孙子）→ 阶段零/三**：先识别书的"势"再动手，战略设计。
- **道（老子）→ 阶段二/六**：概念关系网 > 概念列表；知识自进化闭环。
- **行（论语）→ 阶段四/五**：以用为验，不以记为验。

书道执行本身用**三省六部**治理（中书起草 → 门下审驳 → 尚书六部执行），详见 `references/06-governance.md`。
