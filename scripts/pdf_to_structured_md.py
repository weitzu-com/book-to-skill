#!/usr/bin/env python3
"""pdf_to_structured_md.py — 任意 PDF → 结构化 Markdown（书道阶段零首选入口）。

相比 pdf_to_text.sh（pdftotext 扁平文本）的升级：用 OpenDataLoader 产出**带结构**的
Markdown（# 标题层级 / 表格 / 阅读顺序保留），让阶段一章节边界检测近乎白送，
可读率门禁更易过——这是「PDF → 高保真 Skill」的杠杆点。

行为：
  1. 自注入 Homebrew OpenJDK 到 PATH（包是 Java CLI 封装，OpenJDK keg-only 不在默认 PATH）。
  2. 若当前解释器没有 opendataloader_pdf → 自动 re-exec 到 ~/pdf2md/.venv（可用
     $OPENDATALOADER_PYTHON 覆盖）。
  3. 本地快速模式转换（60+ 页/秒）。
  4. 产物字符数过低 = 扫描件无文字层 → 自动起 hybrid OCR server（ocrmac，macOS Vision，
     原生零下载）跑 OCR，再关掉 server。可用 --no-ocr 关闭兜底。

用法:
    python3 pdf_to_structured_md.py <input.pdf> [-o out.md]
                                    [--ocr-lang "zh-Hans,en-US"] [--engine ocrmac]
                                    [--no-ocr]

依赖: opendataloader-pdf[hybrid] + ocrmac（已在 ~/pdf2md/.venv 验证安装）；Homebrew openjdk。
"""
import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

MIN_TEXT = 50            # 去图片引用后的正文字符数低于此 → 判扫描件（无文字层）
HYBRID_PORT = 5002       # convert(hybrid=...) 默认连 localhost:5002，锁定此端口
SERVER_TIMEOUT = 180     # server 初始化 + 首次 OCR 模型加载的最长等待（秒）

_IMG_REF = re.compile(r"!\[[^\]]*\]\([^)]*\)")  # markdown 图片占位


def ensure_java() -> None:
    """OpenJDK（Homebrew）keg-only，默认不在 PATH。
    注意：macOS 自带 /usr/bin/java 是 stub（无 JRE 也存在），shutil.which 会被骗，
    所以优先把 Homebrew openjdk 前插进 PATH 盖过 stub。"""
    for cand in ("/opt/homebrew/opt/openjdk/bin", "/usr/local/opt/openjdk/bin"):
        if (pathlib.Path(cand) / "java").exists():
            os.environ["PATH"] = cand + os.pathsep + os.environ.get("PATH", "")
            home = pathlib.Path(cand).parent / "libexec/openjdk.jdk/Contents/Home"
            if home.exists():
                os.environ.setdefault("JAVA_HOME", str(home))
            return
    # 没有 Homebrew openjdk → 验证 PATH 上的 java 能否真正运行（绕开 stub）
    if shutil.which("java"):
        try:
            if subprocess.run(["java", "-version"], capture_output=True).returncode == 0:
                return
        except OSError:
            pass
    sys.exit("✗ 找不到可用的 java。请先运行: brew install openjdk")


def ensure_opendataloader_env() -> None:
    """当前解释器没装 opendataloader → re-exec 到 pdf2md venv。"""
    try:
        import opendataloader_pdf  # noqa: F401
        return
    except ImportError:
        pass
    # 已 re-exec 过一次仍缺 → 目标 venv 也没装，别再循环
    if os.environ.get("_ODL_REEXEC"):
        sys.exit(
            '✗ 目标 venv 里也没有 opendataloader_pdf。请装:\n'
            '    pip install -U "opendataloader-pdf[hybrid]" ocrmac'
        )
    venv_py = os.path.expanduser(
        os.environ.get("OPENDATALOADER_PYTHON", "~/pdf2md/.venv/bin/python")
    )
    # venv 的 python 是指向 base 的符号链接，不能用 realpath 比相等来防循环（会误判）；用哨兵环境变量
    if pathlib.Path(venv_py).exists():
        os.environ["_ODL_REEXEC"] = "1"
        os.execv(venv_py, [venv_py, os.path.abspath(__file__), *sys.argv[1:]])
    sys.exit(
        '✗ 未找到 opendataloader_pdf。请在某个 venv 装:\n'
        '    pip install -U "opendataloader-pdf[hybrid]" ocrmac\n'
        '  或设 $OPENDATALOADER_PYTHON 指向已装好的 python。'
    )


def server_alive(port: int) -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{port}/", timeout=1)
    except urllib.error.HTTPError:
        return True          # 404/405 等也算活着
    except Exception:
        return False
    return True


def text_chars(md_path: pathlib.Path) -> int:
    """去掉图片占位后的正文字符数 = 真正可读文字量（扫描件只有图片占位→近零）。"""
    if not md_path.exists():
        return 0
    return len(_IMG_REF.sub("", md_path.read_text(errors="ignore")).strip())


def main() -> None:
    ap = argparse.ArgumentParser(description="任意 PDF → 结构化 Markdown（书道阶段零入口）")
    ap.add_argument("input", help="输入 PDF 路径")
    ap.add_argument("-o", "--output", help="输出 .md 路径（默认与输入同名换 .md）")
    ap.add_argument("--ocr-lang", default="zh-Hans,en-US",
                    help="OCR 语种（ocrmac 用 BCP-47，逗号分隔；默认 简中+英）")
    ap.add_argument("--engine", default="ocrmac",
                    help="OCR 引擎：ocrmac(默认/原生零下载) | easyocr | rapidocr | tesseract")
    ap.add_argument("--no-ocr", action="store_true", help="只跑快速模式，不对扫描件兜底 OCR")
    args = ap.parse_args()

    src = pathlib.Path(args.input)
    if not src.is_file():
        sys.exit(f"✗ 找不到输入文件: {src}")
    out = pathlib.Path(args.output) if args.output else src.with_suffix(".md")
    out_dir = out.parent if args.output else src.parent

    import opendataloader_pdf

    # --- 快速模式 ---
    print(f"→ 本地快速模式转换: {src.name}")
    opendataloader_pdf.convert(input_path=[str(src)], output_dir=str(out_dir), format="markdown")
    produced = out_dir / f"{src.stem}.md"
    pre = text_chars(produced)
    print(f"  正文字符数(去图片占位): {pre}")

    if pre >= MIN_TEXT or args.no_ocr:
        verdict = "OK(数字版)" if pre >= MIN_TEXT else "LOW(未OCR)"
        _finalize(produced, out, verdict, pre)
        return

    # --- 扫描件兜底：起 OCR server → 客户端转 → 关 server ---
    print(f"  正文 < {MIN_TEXT} 字 → 判扫描件，启动 hybrid OCR（引擎 {args.engine}，语种 {args.ocr_lang}）…")
    bin_dir = pathlib.Path(sys.executable).parent
    server_cmd = [
        str(bin_dir / "opendataloader-pdf-hybrid"), "--port", str(HYBRID_PORT),
        "--force-ocr", "--ocr-engine", args.engine, "--ocr-lang", args.ocr_lang,
    ]
    started_here = False
    proc = None
    if server_alive(HYBRID_PORT):
        print(f"  复用已在 :{HYBRID_PORT} 运行的 server")
    else:
        proc = subprocess.Popen(server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started_here = True
        print(f"  server 启动中（初始化约 20s，最多等 {SERVER_TIMEOUT}s）…")
        deadline = time.time() + SERVER_TIMEOUT
        while time.time() < deadline:
            if server_alive(HYBRID_PORT):
                break
            if proc.poll() is not None:
                sys.exit("✗ OCR server 启动失败（端口被占或依赖缺失）。")
            time.sleep(2)
        else:
            proc.terminate()
            sys.exit("✗ OCR server 启动超时。")
        print("  server 就绪，开始 OCR…")

    try:
        opendataloader_pdf.convert(input_path=[str(src)], output_dir=str(out_dir),
                                   format="markdown", hybrid="docling-fast")
    finally:
        if started_here and proc:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    post = text_chars(produced)
    # OCR 成功 = 正文从无到有显著长出来（而非仍是空/图片占位）
    verdict = "OK(OCR)" if post > pre + 10 else "FAIL(OCR后仍无文字)"
    _finalize(produced, out, verdict, post)


def _finalize(produced: pathlib.Path, out: pathlib.Path, verdict: str, chars: int | None = None) -> None:
    if produced.exists() and produced.resolve() != out.resolve():
        out.parent.mkdir(parents=True, exist_ok=True)
        produced.replace(out)
    c = chars if chars is not None else text_chars(out)
    print(f"\n[{verdict}] {out}  ({c} 字正文)")
    if verdict.startswith("FAIL") or verdict.startswith("LOW"):
        print("⚠️ 没提取到正文。换 --engine easyocr 重试，或换更优源（见 references/01）。")
        sys.exit(2)
    print("✅ 已得结构化 MD，可按「MD 已优化」最快路径直入阶段一。")
    print("   注：本脚本只做『有没有文字』的量化闸；『可读率≥60%』的语义闸仍由阶段二 Agent/人判。")


if __name__ == "__main__":
    ensure_java()
    ensure_opendataloader_env()
    main()
