#!/usr/bin/env python3
"""
图片搜索脚本 - 使用 DDGS 进行图片搜索和下载

使用方式:
    python image_search.py "搜索关键词" --max_results 10 --size Large --download ./images
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

try:
    from ddgs import DDGS
except ImportError:
    print("错误: 请先安装 ddgs 库")
    print("运行: pip install ddgs")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("错误: 请先安装 requests 库")
    print("运行: pip install requests")
    sys.exit(1)


def search_images(
    query: str,
    max_results: int = 10,
    region: str = "zh-cn",
    safesearch: str = "moderate",
    size: Optional[str] = None,
    color: Optional[str] = None,
    type_image: Optional[str] = None,
    layout: Optional[str] = None,
    license_image: Optional[str] = None,
) -> list[dict]:
    """
    执行图片搜索

    Args:
        query: 搜索关键词
        max_results: 最大结果数
        region: 搜索区域
        safesearch: 安全搜索级别
        size: 图片尺寸 (Small/Medium/Large/Wallpaper)
        color: 颜色过滤
        type_image: 图片类型 (photo/clipart/gif/transparent/line)
        layout: 布局 (Square/Tall/Wide)
        license_image: 版权过滤

    Returns:
        搜索结果列表
    """
    ddgs = DDGS()

    try:
        # 构建搜索参数
        kwargs = {
            "region": region,
            "safesearch": safesearch,
            "max_results": max_results,
        }

        if size:
            kwargs["size"] = size
        if color:
            kwargs["color"] = color
        if type_image:
            kwargs["type_image"] = type_image
        if layout:
            kwargs["layout"] = layout
        if license_image:
            kwargs["license_image"] = license_image

        results = ddgs.images(query, **kwargs)  # query 作为第一个位置参数
        return list(results) if results else []

    except Exception as e:
        print(f"错误: 搜索图片时出错: {e}", file=sys.stderr)
        return []


def get_file_extension(url: str, content_type: Optional[str] = None) -> str:
    """
    从 URL 或 Content-Type 推断文件扩展名

    Args:
        url: 图片 URL
        content_type: HTTP Content-Type 头

    Returns:
        文件扩展名（包含点号）
    """
    # 尝试从 Content-Type 获取
    if content_type:
        type_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
            "image/bmp": ".bmp",
        }
        for mime, ext in type_map.items():
            if mime in content_type:
                return ext

    # 尝试从 URL 路径获取
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"]:
        if path.endswith(ext):
            return ext if ext != ".jpeg" else ".jpg"

    # 默认使用 jpg
    return ".jpg"


def download_image(
    url: str,
    save_path: Path,
    timeout: int = 30,
) -> Optional[Path]:
    """
    下载单张图片，优雅处理异常

    Args:
        url: 图片 URL
        save_path: 保存路径（不含扩展名）
        timeout: 超时时间（秒）

    Returns:
        实际保存的文件路径，失败返回 None
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        # 获取正确的扩展名
        content_type = response.headers.get("Content-Type", "")
        ext = get_file_extension(url, content_type)

        # 最终文件路径
        final_path = save_path.with_suffix(ext)

        # 写入文件
        with open(final_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return final_path

    except requests.exceptions.Timeout:
        print(f"  ⚠ 下载超时: {url[:60]}...", file=sys.stderr)
    except requests.exceptions.HTTPError as e:
        print(f"  ⚠ HTTP 错误 {e.response.status_code}: {url[:60]}...", file=sys.stderr)
    except requests.exceptions.ConnectionError:
        print(f"  ⚠ 连接失败: {url[:60]}...", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"  ⚠ 请求异常: {e}", file=sys.stderr)
    except IOError as e:
        print(f"  ⚠ 文件写入失败: {e}", file=sys.stderr)

    return None


def download_images(
    results: list[dict],
    download_dir: str,
    delay: float = 0.5,
) -> list[dict]:
    """
    批量下载图片

    Args:
        results: 搜索结果列表
        download_dir: 下载目录
        delay: 下载间隔（秒）

    Returns:
        更新后的结果列表（包含 local_path）
    """
    download_path = Path(download_dir)
    download_path.mkdir(parents=True, exist_ok=True)

    print(f"正在下载 {len(results)} 张图片到 {download_path}", file=sys.stderr)

    success_count = 0
    for i, result in enumerate(results, 1):
        image_url = result.get("image", "")
        if not image_url:
            continue

        # 生成文件名（不含扩展名）
        base_name = f"image_{i:03d}"
        save_path = download_path / base_name

        print(f"  [{i}/{len(results)}] 下载中...", file=sys.stderr)

        final_path = download_image(image_url, save_path)

        if final_path:
            result["local_path"] = str(final_path)
            success_count += 1
        else:
            result["local_path"] = None

        # 下载间隔，避免触发限制
        if i < len(results):
            time.sleep(delay)

    print(f"下载完成: {success_count}/{len(results)} 成功", file=sys.stderr)
    return results


def format_output(
    query: str,
    results: list[dict],
) -> str:
    """
    格式化输出为 JSON

    Args:
        query: 搜索关键词
        results: 搜索结果列表

    Returns:
        JSON 字符串
    """
    output = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "total_results": len(results),
        "results": [
            {
                "title": r.get("title", ""),
                "image": r.get("image", ""),
                "thumbnail": r.get("thumbnail", ""),
                "url": r.get("url", ""),
                "source": r.get("source", ""),
                "width": r.get("width"),
                "height": r.get("height"),
                "local_path": r.get("local_path"),
            }
            for r in results
        ],
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="图片搜索脚本 - 使用 DDGS 进行图片搜索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python image_search.py "科技插图"
    python image_search.py "风景摄影" --size Large --layout Wide
    python image_search.py "卡通头像" --type clipart --download ./images
        """,
    )

    parser.add_argument("query", help="搜索关键词")
    parser.add_argument(
        "--max_results",
        type=int,
        default=10,
        help="最大结果数 (默认: 10)",
    )
    parser.add_argument(
        "--region",
        default="zh-cn",
        help="搜索区域 (默认: zh-cn)",
    )
    parser.add_argument(
        "--size",
        choices=["Small", "Medium", "Large", "Wallpaper"],
        help="图片尺寸过滤",
    )
    parser.add_argument(
        "--color",
        help="颜色过滤 (如: Red, Blue, Green, Monochrome)",
    )
    parser.add_argument(
        "--type",
        dest="type_image",
        choices=["photo", "clipart", "gif", "transparent", "line"],
        help="图片类型过滤",
    )
    parser.add_argument(
        "--layout",
        choices=["Square", "Tall", "Wide"],
        help="布局过滤",
    )
    parser.add_argument(
        "--license",
        dest="license_image",
        help="版权过滤 (如: any, Public, Share, Modify)",
    )
    parser.add_argument(
        "--safesearch",
        choices=["on", "moderate", "off"],
        default="moderate",
        help="安全搜索级别 (默认: moderate)",
    )
    parser.add_argument(
        "--download",
        metavar="DIR",
        help="下载图片到指定目录",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="输出 JSON 文件路径 (默认: 标准输出)",
    )

    args = parser.parse_args()

    print(f"正在搜索图片: {args.query}", file=sys.stderr)

    # 执行搜索
    results = search_images(
        query=args.query,
        max_results=args.max_results,
        region=args.region,
        safesearch=args.safesearch,
        size=args.size,
        color=args.color,
        type_image=args.type_image,
        layout=args.layout,
        license_image=args.license_image,
    )

    print(f"找到 {len(results)} 张图片", file=sys.stderr)

    # 下载图片（如果指定）
    if args.download and results:
        results = download_images(results, args.download)

    # 格式化输出
    output = format_output(args.query, results)

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
