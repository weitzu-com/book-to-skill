#!/usr/bin/env python3
"""detect_structure.py — 从纯文本检测章节标题，输出 markdown 结构骨架。

匹配规则:
  - 中文章节:  第[一二三四五六七八九十百零0-9]+[章节回讲条]
  - 英文章节:  Chapter <数字>
  - 编号标题:  行首 <数字>. 或 <数字>、 后接非空字符
  - markdown:  行首 1-3 个 # 后接空格

用法:
    python3 detect_structure.py <full_text.txt>

输出到 stdout: `# <文件名> 结构骨架` + 统计 + 每个标题 `## <标题>  <!-- line N -->`。
无匹配时提示可能是扫描版、需先 OCR。
"""
import os
import re
import sys

PATTERNS = [
    re.compile(r"^\s*第[一二三四五六七八九十百零0-9]+[章节回讲条]"),
    re.compile(r"^\s*Chapter\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*\d+[.、]\s+\S"),
    re.compile(r"^\s*#{1,3}\s+\S"),
]


def is_heading(line):
    return any(p.search(line) for p in PATTERNS)


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("用法: python3 detect_structure.py <full_text.txt>\n")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.isfile(path):
        sys.stderr.write(f"错误: 找不到文件: {path}\n")
        sys.exit(1)

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total_lines = len(lines)
    headings = []
    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        if is_heading(line):
            headings.append((i, line.strip()))

    name = os.path.basename(path)
    out = []
    out.append(f"# {name} 结构骨架")
    out.append("")

    if not headings:
        out.append(f"> 共扫描 {total_lines} 行，未检测到任何章节标题。")
        out.append(">")
        out.append("> 可能原因: 这是扫描版 PDF（无文字层），需先 OCR 提取文字。")
        out.append("> 处理: python3 scripts/extract_pdf.py book.pdf > full_text.txt")
        out.append("> 或: tesseract chi_sim OCR 后再检测。")
        print("\n".join(out))
        return

    out.append(f"> 共检测到 {len(headings)} 章 / 扫描 {total_lines} 行。")
    out.append("")
    for line_no, title in headings:
        out.append(f"## {title}  <!-- line {line_no} -->")

    print("\n".join(out))


if __name__ == "__main__":
    main()
