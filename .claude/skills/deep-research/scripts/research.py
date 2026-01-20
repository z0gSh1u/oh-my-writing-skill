#!/usr/bin/env python3
"""
深度研究脚本 - 使用 DDGS 进行多后端联网搜索

使用方式:
    python research.py "搜索主题" --max_results 20 --timelimit m --region zh-cn
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

try:
    from ddgs import DDGS
except ImportError:
    print("错误: 请先安装 ddgs 库")
    print("运行: pip install ddgs")
    sys.exit(1)


def expand_keywords(query: str) -> list[str]:
    """
    扩展搜索关键词，从多个角度覆盖主题

    Args:
        query: 原始搜索主题

    Returns:
        扩展后的关键词列表
    """
    # 基础扩展后缀
    suffixes = [
        "",  # 原始关键词
        " 最新",
        " 教程",
        " 评测",
        " 是什么",
    ]

    keywords = []
    for suffix in suffixes:
        kw = f"{query}{suffix}".strip()
        if kw not in keywords:
            keywords.append(kw)

    return keywords


def search_single_keyword(
    ddgs,
    keyword: str,
    max_results: int = 10,
    timelimit: Optional[str] = None,
    region: str = "zh-cn",
) -> list[dict]:
    """
    对单个关键词执行搜索

    Args:
        ddgs: DDGS 实例
        keyword: 搜索关键词
        max_results: 最大结果数
        timelimit: 时间限制 (d/w/m/y)
        region: 搜索区域

    Returns:
        搜索结果列表
    """
    try:
        results = ddgs.text(
            keyword,  # 第一个参数直接是 query 字符串
            region=region,
            safesearch="moderate",
            timelimit=timelimit,
            max_results=max_results,
            backend="bing",  # 使用 Bing 后端
        )
        return list(results) if results else []
    except Exception as e:
        print(f"警告: 搜索 '{keyword}' 时出错: {e}", file=sys.stderr)
        return []


def deduplicate_results(results: list[dict]) -> list[dict]:
    """
    按 URL 去重搜索结果

    Args:
        results: 原始结果列表

    Returns:
        去重后的结果列表
    """
    seen_urls = set()
    unique_results = []

    for result in results:
        url = result.get("href", "")
        # 标准化 URL（移除尾部斜杠和参数）
        parsed = urlparse(url)
        normalized = f"{parsed.netloc}{parsed.path.rstrip('/')}"

        if normalized and normalized not in seen_urls:
            seen_urls.add(normalized)
            unique_results.append(result)

    return unique_results


def format_markdown_report(
    query: str,
    keywords: list[str],
    results: list[dict],
) -> str:
    """
    将搜索结果格式化为 Markdown 报告

    Args:
        query: 原始搜索主题
        keywords: 使用的关键词列表
        results: 搜索结果列表

    Returns:
        Markdown 格式的报告
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# 研究报告：{query}",
        "",
        "## 搜索概览",
        f"- 搜索时间：{now}",
        f"- 关键词：{', '.join(keywords)}",
        f"- 结果数量：{len(results)} 条（已去重）",
        "",
        "## 核心发现",
        "",
    ]

    # 添加每个结果
    for i, result in enumerate(results, 1):
        # 调试：打印第一个结果的所有字段
        if i == 1:
            print(f"\n调试信息 - 结果对象包含的字段:", file=sys.stderr)
            for key, value in result.items():
                preview = str(value)[:100] if value else "None"
                print(f"  {key}: {preview}", file=sys.stderr)
            print("", file=sys.stderr)

        title = result.get("title", "无标题")
        body = result.get("body", "无摘要")
        href = result.get("href", "#")

        lines.extend(
            [
                f"### {i}. {title}",
                "",
                body,
                "",
                f"> 来源：[{title}]({href})",
                "",
            ]
        )

    # 添加参考资料汇总
    lines.extend(
        [
            "---",
            "",
            "## 参考资料",
            "",
        ]
    )

    for i, result in enumerate(results, 1):
        title = result.get("title", "无标题")
        href = result.get("href", "#")
        lines.append(f"{i}. [{title}]({href})")

    return "\n".join(lines)


def format_json_output(
    query: str,
    keywords: list[str],
    results: list[dict],
) -> str:
    """
    将搜索结果格式化为 JSON

    Args:
        query: 原始搜索主题
        keywords: 使用的关键词列表
        results: 搜索结果列表

    Returns:
        JSON 格式的结果
    """
    output = {
        "query": query,
        "keywords": keywords,
        "timestamp": datetime.now().isoformat(),
        "total_results": len(results),
        "results": results,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="深度研究脚本 - 使用 DDGS 进行联网搜索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python research.py "AI 写作工具"
    python research.py "Python 异步编程" --max_results 20 --timelimit w
    python research.py "机器学习入门" --region us-en --output research.md
        """,
    )

    parser.add_argument("query", help="搜索主题")
    parser.add_argument(
        "--max_results",
        type=int,
        default=10,
        help="每个关键词的最大结果数 (默认: 10)",
    )
    parser.add_argument(
        "--timelimit",
        choices=["d", "w", "m", "y"],
        default=None,
        help="时间限制: d=天, w=周, m=月, y=年",
    )
    parser.add_argument(
        "--region",
        default="zh-cn",
        help="搜索区域 (默认: zh-cn)",
    )
    parser.add_argument(
        "--no-expand",
        action="store_true",
        help="禁用关键词扩展",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="输出文件路径 (默认: 标准输出)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式 (默认: markdown)",
    )

    args = parser.parse_args()

    # 生成关键词
    if args.no_expand:
        keywords = [args.query]
    else:
        keywords = expand_keywords(args.query)

    print(f"正在搜索: {', '.join(keywords)}", file=sys.stderr)

    # 执行搜索
    ddgs = DDGS()
    all_results = []

    for keyword in keywords:
        print(f"  - 搜索: {keyword}", file=sys.stderr)
        results = search_single_keyword(
            ddgs=ddgs,
            keyword=keyword,
            max_results=args.max_results,
            timelimit=args.timelimit,
            region=args.region,
        )
        all_results.extend(results)

    # 去重
    unique_results = deduplicate_results(all_results)
    print(f"共获取 {len(unique_results)} 条结果（去重后）", file=sys.stderr)

    # 格式化输出
    if args.format == "json":
        output = format_json_output(args.query, keywords, unique_results)
    else:
        output = format_markdown_report(args.query, keywords, unique_results)

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
