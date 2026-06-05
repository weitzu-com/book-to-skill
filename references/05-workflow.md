---
domain: AI开发
type: 步骤
maturity: 已验证
version: v2.3
---

# 阶段二/四 · Workflow 并行策略

> **一句话**：章节解析用 `pipeline`（先到先出、单章失败不阻塞）；references 六件套用 `parallel`（6 文件无相互依赖、需全部完成再合并）。
> 何时上 Workflow 取决于**章节数**与**是否需要汇总后再继续**。

---

## 1. 何时用 Workflow vs 单 Agent

| 规模 / 任务 | 策略 | 理由 |
|------------|------|------|
| ≤8 章 | **单 Agent 全量** | 上下文装得下，并行的协调成本 > 收益 |
| 9-15 章 | **Workflow pipeline 并行** | 每章一个 Agent，先到先出，单章失败 null 不阻塞 |
| 16-25 章 | **pipeline 分批** | 一次并发 6-8 章，分 2-3 批，防止 Agent 数爆炸 |
| 25+ 章 | **pipeline 分批 + 合并** | 分批 pipeline 解析后，单 Agent 综合阶段统一合并 |
| references 六件套编写 | **parallel 6 并行** | 6 个文件互不依赖，可同时写，全部完成后合并 |

**判据**：要"先到先出、容忍部分失败"→ pipeline；要"全部齐了再往下"→ parallel。

---

## 2. pipeline vs parallel：区别与选择

| 维度 | `pipeline` | `parallel` |
|------|-----------|-----------|
| 完成语义 | 先到先出，谁先好谁先进结果 | 等全部完成，一次性返回 |
| 失败处理 | 单元失败返 `null`，**不阻塞其他单元** | 任一失败可能拖累整体合并 |
| 典型场景 | **章节解析**（章与章独立、允许个别失败补救） | **references 编写**（6 件套要齐才能交付） |
| 收尾动作 | `results.filter(Boolean)` 过滤失败章后继续 | 全部 resolve 后进入合并/校验 |

**选择规则**：
- **章节解析 → pipeline**。每章是独立单元，第 7 章 OCR 不清失败了，不该让前 6 章也卡住；失败章用 `.filter(Boolean)` 滤掉，记下来后续用独立 Agent 补解析。
- **references 六件套 → parallel**。concepts / frameworks / methods / principles / cases / knowledge_graph 必须同时齐全才算阶段四完成，所以用 parallel 等全部完成再合并校验。

---

## 3. 标准 Workflow 脚本模板

> 复用此结构。StructuredOutput 的 JSON Schema 放**顶层**，阶段二解析用 pipeline 每章并行，阶段二综合用单 Agent 一次完成。

```javascript
// ===== 顶层：StructuredOutput JSON Schema（强制每章 Agent 输出结构化 JSON）=====
const CHAPTER_SCHEMA = {
  type: "object",
  required: ["chapter", "concepts", "frameworks", "methods", "principles"], // required 写全
  properties: {
    chapter:    { type: "string" },
    concepts:   { type: "array", items: { type: "object",
                    required: ["name", "definition", "source"],          // L1 概念
                    properties: { name:{type:"string"}, definition:{type:"string"}, source:{type:"string"} } } },
    frameworks: { type: "array", items: { type: "object",
                    required: ["name", "elements", "chapter_ref"] } },    // L2 框架
    methods:    { type: "array", items: { type: "object",
                    required: ["name", "steps", "io", "verify"] } },      // L3 方法
    principles: { type: "array", items: { type: "object",
                    required: ["statement", "boundary"] } }               // L4 原则
  }
};

const meta = {
  name: "book-parse",
  phases: ["Parse", "Synthesize"]   // 阶段二：先逐章解析，再综合
};

// ===== 阶段 Parse：pipeline 每章并行，schema 强制 JSON，失败章返 null =====
phase("Parse", async () => {
  const results = await pipeline(CHAPTERS, ch =>
    agent({
      prompt: `提取本章四层知识 L1概念→L2框架→L3方法→L4原则，案例作为锚点标注出处。\n章节正文：\n${ch.text}`,
      output: { type: "StructuredOutput", schema: CHAPTER_SCHEMA },
      onError: () => null            // 单章失败返 null，不阻塞其他章
    })
  );
  return results.filter(Boolean);    // 过滤失败章，后续用独立 Agent 补解析
});

// ===== 阶段 Synthesize：单 Agent 综合，合并知识图谱 + 跨章关联，一次完成 =====
phase("Synthesize", async (parsed) => {
  return await agent({
    prompt: `把以下各章结构化结果合并：去重概念、连边构建知识图谱、识别跨章关联与隐含假设，
             输出六件套草稿与完整度热图。\n${JSON.stringify(parsed)}`
    // 综合阶段不再分阶段，一次完成
  });
});
```

---

## 4. 关键经验 5 条

1. **pipeline > parallel（解析阶段）**：章节解析永远用 pipeline，享受先到先出 + 容忍单章失败；parallel 只留给"必须全齐"的 references 编写。
2. **StructuredOutput 的 `required` 字段写全**：required 漏写会让 Agent 偷懒省略 methods/principles，导致后续合并时知识层缺失，难以察觉。
3. **pipeline 单章失败不阻塞**：`onError: () => null` + `results.filter(Boolean)`，一章失败只损失一章，不让整本书卡死。
4. **补解析用独立 Agent**：被 filter 掉的失败章，单独起一个 Agent 重试/换策略（如换 OCR 源），别塞回原 pipeline 拖慢主流程。
5. **综合阶段一次完成**：合并知识图谱 + 跨章关联用单 Agent 一次性做完，不要再拆成子阶段——综合本身需要全局上下文，拆了反而丢关联。

---

## 5. 效率基准表（5 本真实书）

| 书 | 格式 | 页数 | Workflow 总耗时 |
|----|------|------|----------------|
| 会计七原则 | MD | 135 页 | ~30min |
| Claude Code 手册 | PDF 文本型 | 75 页 | ~40min |
| 吉拉德（Joe Girard）| PDF-OCR | 190 页 | ~60min |
| 经营十二条 | PDF 扫描 | 258 页 | ~50min |
| Harness 工程之道 | PDF 扫描 | 314 页 | ~70min（Workflow）|

**阶段二/四：单 Agent vs 手动 3 Agent vs Workflow pipeline 对比**（以 314 页 Harness 工程之道为例）：

| 方式 | 阶段二解析 | 阶段四编写 | Agent 数 | 备注 |
|------|-----------|-----------|---------|------|
| 单 Agent 全量 | ~55min | ~30min | 1 | 长书上下文溢出，后期章质量塌方 |
| 手动 3 Agent | ~35min | ~22min | 3 | 人工切分/拼接，协调成本高、易漏章 |
| **Workflow pipeline** | **~22min** | **~12min** | **章数动态（pipeline）+ 6（parallel）** | 先到先出 + 失败隔离 + 六件套并写，最快且最稳 |

**结论**：≤8 章用单 Agent 省心；9 章起 Workflow pipeline 的收益随章数与页数显著放大，扫描版长书（258/314 页）提速最明显。
