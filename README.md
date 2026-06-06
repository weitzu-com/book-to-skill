# book-to-skill (书道)

> Compile a **book** into a reusable **Claude Code Skill** — a pipeline that distills a book's *judgment* into a capability Claude can call.
> 把「一本书」编译成「一个 Claude Code Skill」的流水线——把书的**判断力**提炼成 Claude 可随时调用的能力。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Status: validated](https://img.shields.io/badge/status-validated%20on%205%20books-success.svg)](#validation-track-record--验证记录)
[![Pipeline: 7 stages](https://img.shields.io/badge/pipeline-7%20stages-orange.svg)](#the-7-stage-pipeline--七阶段流水线)
[![Version: v2.4](https://img.shields.io/badge/version-v2.4-blue.svg)](#changelog--更新记录)

---

## What is this / 这是什么

**EN** — `book-to-skill` takes one book (PDF, scanned/OCR PDF, EPUB, Markdown, or TXT) and compiles it into a single, reusable Claude Code Skill: a `SKILL.md` plus a six-file `references/` knowledge set plus helper `scripts/`. The output is not a stored copy of the book — it is a capability Claude Code can invoke on demand.

**中文** — 「书道」（book-to-skill）是一条把一本书（PDF / 扫描版 PDF / EPUB / Markdown / TXT）编译成一个可长期复用的 Claude Code Skill 的流水线。产物是 `SKILL.md` + `references/` 六件套 + `scripts/`。它不是把书"存起来"，而是把书做成 Claude Code 可随时调用的**能力**。

---

## Why / 第一性原理

**The value of a book = its ability to change how the reader *judges and acts*.**

So a book-skill is **not** graded on "how much it memorized." It is graded on **"can it make a decision in a new situation that is faithful to the spirit of the original book?"** Judgment, not recall, is the acceptance criterion.

> 一本书的价值 = 它改变读者「如何判断与行动」的能力。
> 因此**不以"记住了多少"为验收，以"能否在新场景里做出符合原书精神的判断"为验收**。

---

## The 7-stage pipeline / 七阶段流水线

```
Stage 0  Preprocess decision   判格式 + 冲突检测（先判断，再动手）
Stage 1  Structuring           → book_structured.md（章节边界 + 全角→半角）
Stage 2  Deep parse            多 Agent 并行四层提取：概念→框架→方法→原则
Stage 3  Cognitive architecture 五要素：身份/知识分配/能力边界/行为模式/交互协议
Stage 4  Skill authoring       SKILL.md（<500行）+ references 六件套 + scripts
Stage 5  5-dimension validation 覆盖度/关系/应用/判断/边界——以"用"为验，不以"记"为验
Stage 6  Archive & close loop  知识图谱 + 工作日志 + 索引
```

| Stage | EN | 中文 |
|-------|----|----|
| 0 | Preprocess & conflict-detect | 预处理决策 + 冲突检测 |
| 1 | Structuring (chapter boundaries, full→half-width) | 结构化 |
| 2 | Multi-Agent parallel 4-layer parse | 多 Agent 并行四层解析 |
| 3 | Cognitive architecture (5 elements) | 认知架构五要素 |
| 4 | SKILL.md + references six-pack | SKILL 编写 + references 六件套 |
| 5 | 5-dimension validation (use, not recall) | 五维验证 |
| 6 | Archive: knowledge graph + log + index | 归档闭环 |

---

## Quick start / 快速开始

**Install / 安装**

```bash
# Option A — clone directly into your skills dir
git clone https://github.com/weitzu-com/book-to-skill.git \
  ~/.claude/skills/book-to-skill

# Option B — clone elsewhere, then symlink (or copy)
git clone https://github.com/weitzu-com/book-to-skill.git
ln -s "$(pwd)/book-to-skill" ~/.claude/skills/book-to-skill
```

Optional script dependencies:

```bash
pip install pymupdf        # extract_pdf.py (embedded OCR-layer extraction)
brew install poppler       # pdftotext, used by pdf_to_text.sh
brew install tesseract     # optional: OCR fallback for scans with no text layer
```

**Trigger / 触发** — just tell Claude Code to make a skill out of a book and give it the path:

```
把这本书做成 skill：/path/to/book.pdf
Make this book into a skill: /path/to/book.pdf
```

Claude Code loads `book-to-skill` and runs the 7-stage pipeline end to end.

---

## Repo layout / 目录结构

```
book-to-skill/
├── SKILL.md                  # Pipeline entry: 7 stages, decision trees, routing table
├── README.md                 # This file
├── LICENSE                   # MIT
├── references/               # On-demand knowledge (loaded by SKILL.md routing)
│   ├── 00-pipeline.md        #   Per-stage done-criteria + failure modes
│   ├── 01-preprocess.md      #   Format detection, scanned-PDF OCR, chapter boundaries
│   ├── 02-parse.md           #   Agent prompts, division of labor, 4-layer extraction
│   ├── 03-authoring.md       #   Cognitive architecture + SKILL.md + six-pack how-to
│   ├── 04-validation.md      #   5-dimension criteria + anti-error checklist
│   ├── 05-workflow.md        #   Workflow parallelism scripts + efficiency benchmarks
│   └── 06-governance.md      #   Three-Departments-Six-Ministries governance
├── scripts/
│   ├── pdf_to_text.sh        # Text PDF → TXT (keeps layout, full→half-width)
│   ├── extract_pdf.py        # Scanned PDF → text via PyMuPDF embedded OCR layer
│   ├── detect_structure.py   # TXT → detect chapter boundaries → structured skeleton
│   └── check_skill.py        # 5-dimension structural validation of a produced skill
└── templates/                # Skeleton templates for the produced skill
    ├── SKILL.template.md     #   SKILL.md skeleton (placeholders + ironclad rules)
    └── references/           #   Six-pack reference stubs
```

---

## Scripts / 脚本

| Script | Purpose / 用途 | Example |
|--------|----------------|---------|
| `pdf_to_text.sh` | Text-type PDF → TXT, preserving layout and converting full-width to half-width characters. 文本型 PDF 转 TXT。 | `bash scripts/pdf_to_text.sh book.pdf` |
| `extract_pdf.py` | Pull the embedded OCR text layer out of a scanned PDF (PyMuPDF; ~258 pages in <30s). 扫描版 PDF 提取嵌入 OCR 文字层。 | `python3 scripts/extract_pdf.py book.pdf > full_text.txt` |
| `detect_structure.py` | Detect chapter boundaries in a TXT and emit a structured skeleton. 检测章节边界 → 结构化骨架。 | `python3 scripts/detect_structure.py full_text.txt` |
| `check_skill.py` | Run 5-dimension structural validation on a produced skill (line count, concept count, isolated nodes, six-pack completeness, routing-load directives). 对产出 skill 做结构验证。 | `python3 scripts/check_skill.py <skill_dir>` |

> **Note / 注意**: `check_skill.py` validates a **skill produced by this pipeline** (a book compiled into a skill), *not* this meta-skill repo itself. Running it against `book-to-skill/` will report the six-pack (`concepts/frameworks/methods/principles/cases/knowledge_graph`) as missing — this is **expected**, because `book-to-skill` is the compiler, not a book-derived skill. `check_skill.py` 校验的是「书道产出的成品 skill」，对本仓库自身运行会报六件套缺失，属预期。

**Dependencies / 依赖**: PyMuPDF (`pip install pymupdf`) for `extract_pdf.py`; `pdftotext` from poppler for `pdf_to_text.sh`; `tesseract` (optional) for OCR fallback on scans without an embedded text layer.

---

## Validation track record / 验证记录

Five real books, MD / text-PDF / scanned-PDF, 135–314 pages, full conversion in 30–85 minutes.

| Book / 书 | Format / 格式 | Pages / 页数 | Time / 用时 |
|-----------|---------------|--------------|-------------|
| 会计七原则 (7 Principles of Accounting) | Markdown | 135 | ~30 min |
| Claude Code 手册 (Claude Code Manual) | PDF (text) | 75 | ~40 min |
| Joe Girard (How to Sell Anything) | PDF (OCR) | 190 | ~60 min |
| 经营十二条 (12 Management Principles) | PDF (scanned) | 258 | ~50 min |
| Harness 工程之道 (The Harness Way) | PDF (scanned) | 314 | ~70 min (Workflow parallel) |

---

## Governance / 治理

The pipeline governs itself with a **Three Departments / Six Ministries** model (中书起草 *draft* → 门下审驳 *review & veto* → 尚书六部执行 *execute via six ministries*): drafting proposes, the reviewing department can reject, and the six executing ministries carry out the work. Full details in [`references/06-governance.md`](./references/06-governance.md).

---

## Changelog / 更新记录

- **v2.4** — Provenance gate / 溯源门禁: every L1–L4 element must trace to a real location in the book; un-sourceable items are marked `[待核]` and never fabricated, plus a random 5-element source spot-check before validation. 每个要素须溯源到书中真实位置，溯源不到标 `[待核]` 绝不编造；五维验证前先随机抽 5 要素回原书核对。
- **v2.3** — 5-book validated 7-stage pipeline (MD / text-PDF / scanned-PDF, 135–314 pp). 经五书验证的七阶段流水线。

---

## License

[MIT](./LICENSE) © 2026 weitzu-com
