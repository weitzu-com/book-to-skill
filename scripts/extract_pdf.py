#!/usr/bin/env python3
"""extract_pdf.py — 用 PyMuPDF 把 PDF 每页文字提取到 stdout。

页间用分隔符 `\n\n----- page N -----\n\n` 区隔。支持可选页范围。
扫描版 PDF 若含嵌入 OCR 文字层，PyMuPDF 可直接提取。

用法:
    python3 extract_pdf.py <input.pdf> [--pages A-B]

示例:
    python3 extract_pdf.py book.pdf
    python3 extract_pdf.py book.pdf --pages 10-25 > slice.txt

依赖: PyMuPDF (import fitz)，缺失时提示 pip install pymupdf
"""
import argparse
import sys


def parse_pages(spec, total):
    """把 'A-B' 解析为 0-based 页索引列表；None 表示全部。"""
    if not spec:
        return list(range(total))
    spec = spec.strip()
    if "-" in spec:
        a, b = spec.split("-", 1)
        start = int(a)
        end = int(b)
    else:
        start = end = int(spec)
    # 用户用 1-based，转 0-based 并裁剪到有效范围
    start = max(1, start)
    end = min(total, end)
    if start > end:
        return []
    return list(range(start - 1, end))


def main():
    parser = argparse.ArgumentParser(
        description="用 PyMuPDF 把 PDF 每页文字提取到 stdout。"
    )
    parser.add_argument("input", help="输入 PDF 路径")
    parser.add_argument(
        "--pages", default=None, help="可选页范围，如 10-25 或 7（1-based，含端点）"
    )
    args = parser.parse_args()

    try:
        import fitz  # PyMuPDF；放在运行时导入，便于无依赖也能编译
    except ImportError:
        sys.stderr.write(
            "错误: 未安装 PyMuPDF。请先安装:\n    pip install pymupdf\n"
        )
        sys.exit(1)

    try:
        doc = fitz.open(args.input)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"错误: 无法打开 PDF: {args.input}\n  {exc}\n")
        sys.exit(1)

    total = doc.page_count
    indices = parse_pages(args.pages, total)
    if not indices:
        sys.stderr.write(f"警告: 页范围在 1-{total} 内无有效页。\n")
        sys.exit(1)

    for idx in indices:
        page = doc.load_page(idx)
        text = page.get_text()
        sys.stdout.write(f"\n\n----- page {idx + 1} -----\n\n")
        sys.stdout.write(text)

    doc.close()


if __name__ == "__main__":
    main()
