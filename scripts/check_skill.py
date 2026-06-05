#!/usr/bin/env python3
"""check_skill.py — 对产出的 skill 目录做结构验证。

检查项:
  1. SKILL.md 存在；行数 < 500（超出 WARN）；含 YAML frontmatter 且有 name / description。
  2. references/ 六件套是否齐全:
     concepts / frameworks / methods / principles / cases / knowledge_graph .md。
  3. SKILL.md 是否含 references 加载指令（grep `references/` 出现次数；0 则 FAIL）。
  4. concepts.md 概念数: 以 #/##/- 开头的条目计数，<20 给 WARN。

退出码: 全过 0；有 FAIL 1。

用法:
    python3 check_skill.py <skill_dir>
"""
import os
import re
import sys

OK = "✅"
WARN = "⚠️"
FAIL = "❌"

SIX_PACK = [
    "concepts.md",
    "frameworks.md",
    "methods.md",
    "principles.md",
    "cases.md",
    "knowledge_graph.md",
]


class Report:
    def __init__(self):
        self.lines = []
        self.has_fail = False

    def ok(self, msg):
        self.lines.append(f"{OK} {msg}")

    def warn(self, msg):
        self.lines.append(f"{WARN} {msg}")

    def fail(self, msg):
        self.lines.append(f"{FAIL} {msg}")
        self.has_fail = True


def check_skill_md(skill_dir, rep):
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(path):
        rep.fail("SKILL.md 不存在")
        return None
    rep.ok("SKILL.md 存在")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    lines = content.splitlines()

    # 行数
    n = len(lines)
    if n < 500:
        rep.ok(f"SKILL.md 行数 {n} < 500")
    else:
        rep.warn(f"SKILL.md 行数 {n} >= 500，建议拆分到 references/")

    # frontmatter
    fm = extract_frontmatter(content)
    if fm is None:
        rep.fail("SKILL.md 缺少 YAML frontmatter（--- ... ---）")
    else:
        if re.search(r"^\s*name\s*:", fm, re.MULTILINE):
            rep.ok("frontmatter 含 name 字段")
        else:
            rep.fail("frontmatter 缺少 name 字段")
        if re.search(r"^\s*description\s*:", fm, re.MULTILINE):
            rep.ok("frontmatter 含 description 字段")
        else:
            rep.fail("frontmatter 缺少 description 字段")

    # references 加载指令
    ref_count = content.count("references/")
    if ref_count > 0:
        rep.ok(f"SKILL.md 含 references 加载指令（references/ 出现 {ref_count} 次）")
    else:
        rep.fail("SKILL.md 未引用 references/（写了调不到 = 知识不存在）")

    return content


def extract_frontmatter(content):
    """提取首个 --- ... --- 之间的 YAML，找不到返回 None。"""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if m:
        return m.group(1)
    return None


def check_references(skill_dir, rep):
    ref_dir = os.path.join(skill_dir, "references")
    if not os.path.isdir(ref_dir):
        rep.fail("references/ 目录不存在")
        return
    for fname in SIX_PACK:
        if os.path.isfile(os.path.join(ref_dir, fname)):
            rep.ok(f"references/{fname} 齐全")
        else:
            rep.fail(f"references/{fname} 缺失")


def check_concept_count(skill_dir, rep):
    path = os.path.join(skill_dir, "references", "concepts.md")
    if not os.path.isfile(path):
        # 六件套检查已报缺失，这里跳过
        return
    count = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if line.startswith("#") or line.startswith("-"):
                count += 1
    if count >= 20:
        rep.ok(f"concepts.md 概念条目数 {count} >= 20")
    else:
        rep.warn(f"concepts.md 概念条目数 {count} < 20，覆盖度可能不足")


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("用法: python3 check_skill.py <skill_dir>\n")
        sys.exit(1)

    skill_dir = sys.argv[1]
    if not os.path.isdir(skill_dir):
        sys.stderr.write(f"错误: 不是目录: {skill_dir}\n")
        sys.exit(1)

    rep = Report()
    print(f"=== 检查 skill 目录: {skill_dir} ===\n")

    check_skill_md(skill_dir, rep)
    check_references(skill_dir, rep)
    check_concept_count(skill_dir, rep)

    print("\n".join(rep.lines))

    # 汇总
    n_ok = sum(1 for l in rep.lines if l.startswith(OK))
    n_warn = sum(1 for l in rep.lines if l.startswith(WARN))
    n_fail = sum(1 for l in rep.lines if l.startswith(FAIL))
    print("\n--- 汇总 ---")
    print(f"{OK} 通过 {n_ok}   {WARN} 警告 {n_warn}   {FAIL} 失败 {n_fail}")

    if rep.has_fail:
        print(f"\n结果: {FAIL} 未通过（存在 FAIL 项）")
        sys.exit(1)
    print(f"\n结果: {OK} 通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
