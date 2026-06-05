#!/usr/bin/env bash
#
# pdf_to_text.sh — 文本型 PDF → TXT（保留版式 + 全角转半角）
# 用法: bash pdf_to_text.sh <input.pdf> [output.txt]
# 依赖: pdftotext (poppler), python3
#
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
用法: bash pdf_to_text.sh <input.pdf> [output.txt]

  <input.pdf>   文本型 PDF 路径（扫描版请改用 extract_pdf.py）
  [output.txt]  可选，输出路径；默认与输入同名换 .txt

示例:
  bash pdf_to_text.sh book.pdf
  bash pdf_to_text.sh book.pdf out/book.txt
EOF
  exit 1
}

# --- 参数检查 ---
if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
fi

IN="$1"
if [[ ! -f "$IN" ]]; then
  echo "错误: 找不到输入文件: $IN" >&2
  exit 1
fi

if [[ $# -eq 2 ]]; then
  OUT="$2"
else
  OUT="${IN%.*}.txt"
fi

# --- 依赖检查 ---
if ! command -v pdftotext >/dev/null 2>&1; then
  echo "错误: 未找到 pdftotext。请先安装 poppler:" >&2
  echo "    brew install poppler" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "错误: 未找到 python3。" >&2
  exit 1
fi

# --- 提取（保留版式）---
echo "→ pdftotext -layout 提取中: $IN"
pdftotext -layout "$IN" "$OUT"

# --- 全角转半角（U+FF01-FF5E → ASCII，U+3000 → 普通空格），覆盖写回 ---
echo "→ 全角转半角规范化..."
OUT="$OUT" python3 <<'PY'
import os
path = os.environ["OUT"]
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

out_chars = []
for ch in text:
    code = ord(ch)
    if 0xFF01 <= code <= 0xFF5E:          # 全角 ASCII 可见字符
        out_chars.append(chr(code - 0xFEE0))
    elif code == 0x3000:                  # 全角空格
        out_chars.append(" ")
    else:
        out_chars.append(ch)

with open(path, "w", encoding="utf-8") as f:
    f.write("".join(out_chars))
PY

# --- 报告 ---
LINES=$(wc -l < "$OUT" | tr -d ' ')
echo "✅ 完成"
echo "   输出: $OUT"
echo "   行数: $LINES"
