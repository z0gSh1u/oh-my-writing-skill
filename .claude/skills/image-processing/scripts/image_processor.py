#!/usr/bin/env python3
"""
图片处理脚本 - 在图片中插入配文

支持两种模式:
1. frame (边框模式): 在图片下方添加文字区域
2. sticker (贴纸模式): 在图片内部添加带背景的文字标签

使用方式:
    python image_processor.py input.jpg output.jpg --mode frame --text "配文 🎉"
    python image_processor.py input.jpg output.jpg --mode sticker --text "重点" --position bottom-right
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("错误: 请先安装 Pillow 库")
    print("运行: pip install Pillow")
    sys.exit(1)


# Windows 系统字体路径（按优先级排序）
WINDOWS_FONTS = [
    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",  # 微软雅黑粗体
    "C:/Windows/Fonts/simhei.ttf",  # 黑体
    "C:/Windows/Fonts/simsun.ttc",  # 宋体
    "C:/Windows/Fonts/simkai.ttf",  # 楷体
]


def find_chinese_font(custom_font: Optional[str] = None):
    """
    查找可用的中文字体

    Args:
        custom_font: 自定义字体路径

    Returns:
        字体文件路径
    """
    if custom_font and Path(custom_font).exists():
        return custom_font

    for font_path in WINDOWS_FONTS:
        if Path(font_path).exists():
            return font_path

    # 如果没有找到中文字体，返回 None（将使用 PIL 默认字体）
    print("警告: 未找到中文字体，可能无法正确显示中文", file=sys.stderr)
    return None


def load_font(font_path: Optional[str], size: int):
    """
    加载字体

    Args:
        font_path: 字体文件路径
        size: 字体大小

    Returns:
        字体对象
    """
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"警告: 加载字体失败 ({e})，使用默认字体", file=sys.stderr)

    # 使用 PIL 默认字体
    return ImageFont.load_default()


def parse_color(color_str: str) -> Tuple[int, int, int]:
    """
    解析颜色字符串

    Args:
        color_str: 颜色字符串（名称或 #RRGGBB）

    Returns:
        RGB 元组
    """
    # 常用颜色名称映射
    color_names = {
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "pink": (255, 192, 203),
        "gray": (128, 128, 128),
        "grey": (128, 128, 128),
    }

    color_lower = color_str.lower().strip()

    if color_lower in color_names:
        return color_names[color_lower]

    # 解析 #RRGGBB 格式
    if color_str.startswith("#") and len(color_str) == 7:
        try:
            r = int(color_str[1:3], 16)
            g = int(color_str[3:5], 16)
            b = int(color_str[5:7], 16)
            return (r, g, b)
        except ValueError:
            pass

    print(f"警告: 无法解析颜色 '{color_str}'，使用黑色", file=sys.stderr)
    return (0, 0, 0)


def get_text_size(
    text: str,
    font,
    draw: Optional[ImageDraw.ImageDraw] = None,
):
    """
    获取文本渲染尺寸

    Args:
        text: 文本内容
        font: 字体对象
        draw: ImageDraw 对象（可选）

    Returns:
        (宽度, 高度) 元组
    """
    if draw:
        bbox = draw.textbbox((0, 0), text, font=font)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])

    # 创建临时图像获取尺寸
    temp_img = Image.new("RGB", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def draw_text(
    image: Image.Image,
    position: Tuple[int, int],
    text: str,
    font,
    fill: Tuple[int, int, int],
) -> None:
    """
    绘制文本

    Args:
        image: 图像对象
        position: 文本位置 (x, y)
        text: 文本内容
        font: 字体对象
        fill: 文字颜色
    """
    draw = ImageDraw.Draw(image)
    draw.text(position, text, font=font, fill=fill)


def add_frame_caption(
    image: Image.Image,
    text: str,
    font_path: Optional[str] = None,
    font_size: int = 32,
    bg_color: str = "white",
    text_color: str = "black",
    padding: int = 20,
) -> Image.Image:
    """
    添加底部边框式配文

    Args:
        image: 原始图像
        text: 配文内容
        font_path: 字体路径
        font_size: 字体大小
        bg_color: 背景颜色
        text_color: 文字颜色
        padding: 内边距

    Returns:
        处理后的图像
    """
    font = load_font(font_path, font_size)
    text_width, text_height = get_text_size(text, font)

    # 计算新图像尺寸
    orig_width, orig_height = image.size
    caption_height = text_height + padding * 2
    new_height = int(orig_height + caption_height)

    # 创建新图像
    bg_rgb = parse_color(bg_color)
    new_image = Image.new("RGB", (orig_width, new_height), bg_rgb)

    # 粘贴原图
    new_image.paste(image, (0, 0))

    # 绘制配文
    text_x = int((orig_width - text_width) // 2)
    text_y = orig_height + padding
    text_rgb = parse_color(text_color)

    draw_text(new_image, (text_x, text_y), text, font, text_rgb)

    return new_image


def add_sticker_caption(
    image: Image.Image,
    text: str,
    position: str = "bottom-right",
    font_path: Optional[str] = None,
    font_size: int = 28,
    bg_color: str = "#FFE4B5",
    text_color: str = "#333333",
    opacity: int = 230,
    radius: int = 10,
    margin: int = 20,
    padding: int = 12,
) -> Image.Image:
    """
    添加内部贴纸式配文

    Args:
        image: 原始图像
        text: 配文内容
        position: 位置 (top-left/top-right/bottom-left/bottom-right/center)
        font_path: 字体路径
        font_size: 字体大小
        bg_color: 标签背景色
        text_color: 文字颜色
        opacity: 背景透明度 (0-255)
        radius: 圆角半径
        margin: 距边缘距离
        padding: 标签内边距

    Returns:
        处理后的图像
    """
    # 确保图像是 RGBA 模式
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    font = load_font(font_path, font_size)
    text_width, text_height = get_text_size(text, font)

    # 计算标签尺寸
    label_width = text_width + padding * 2
    label_height = text_height + padding * 2

    # 计算标签位置
    img_width, img_height = image.size

    position_map = {
        "top-left": (margin, margin),
        "top-right": (img_width - label_width - margin, margin),
        "bottom-left": (margin, img_height - label_height - margin),
        "bottom-right": (
            img_width - label_width - margin,
            img_height - label_height - margin,
        ),
        "center": ((img_width - label_width) // 2, (img_height - label_height) // 2),
    }

    label_x, label_y = position_map.get(position, position_map["bottom-right"])

    # 创建标签层
    label_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    label_draw = ImageDraw.Draw(label_layer)

    # 绘制圆角矩形背景
    bg_rgb = parse_color(bg_color)
    bg_rgba = (*bg_rgb, opacity)

    label_draw.rounded_rectangle(
        [label_x, label_y, label_x + label_width, label_y + label_height],
        radius=radius,
        fill=bg_rgba,
    )

    # 合并标签层
    image = Image.alpha_composite(image, label_layer)

    # 绘制文字
    text_x = label_x + padding
    text_y = label_y + padding
    text_rgb = parse_color(text_color)

    draw_text(image, (text_x, text_y), text, font, text_rgb)

    return image


def process_image(
    input_path: str,
    output_path: str,
    mode: str,
    text: str,
    **kwargs,
) -> bool:
    """
    处理单张图片

    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        mode: 处理模式 (frame/sticker)
        text: 配文内容
        **kwargs: 其他参数

    Returns:
        是否成功
    """
    try:
        # 加载图片
        image = Image.open(input_path)

        # 根据模式处理
        if mode == "frame":
            result = add_frame_caption(
                image=image,
                text=text,
                font_path=kwargs.get("font"),
                font_size=kwargs.get("font_size", 32),
                bg_color=kwargs.get("bg_color", "white"),
                text_color=kwargs.get("text_color", "black"),
                padding=kwargs.get("padding", 20),
            )
        elif mode == "sticker":
            result = add_sticker_caption(
                image=image,
                text=text,
                position=kwargs.get("position", "bottom-right"),
                font_path=kwargs.get("font"),
                font_size=kwargs.get("font_size", 28),
                bg_color=kwargs.get("bg_color", "#FFE4B5"),
                text_color=kwargs.get("text_color", "#333333"),
                opacity=kwargs.get("opacity", 230),
                radius=kwargs.get("radius", 10),
                margin=kwargs.get("margin", 20),
                padding=kwargs.get("padding", 12),
            )
        else:
            print(f"错误: 未知模式 '{mode}'", file=sys.stderr)
            return False

        # 保存结果
        # 如果是 RGBA 且输出为 JPG，需要转换
        output_ext = Path(output_path).suffix.lower()
        if output_ext in [".jpg", ".jpeg"] and result.mode == "RGBA":
            # 创建白色背景
            background = Image.new("RGB", result.size, (255, 255, 255))
            background.paste(result, mask=result.split()[3])
            result = background

        result.save(output_path)
        return True

    except Exception as e:
        print(f"错误: 处理图片失败 - {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="图片处理脚本 - 在图片中插入配文",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 底部边框式配文
    python image_processor.py input.jpg output.jpg --mode frame --text "这是配文 🎉"
    
    # 内部贴纸式配文
    python image_processor.py input.jpg output.jpg --mode sticker --text "重点！" --position bottom-right
    
    # 自定义样式
    python image_processor.py input.jpg output.jpg --mode sticker --text "提示" \\
        --bg-color "#E3F2FD" --text-color "#1976D2" --font-size 24
        """,
    )

    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("output", help="输出图片路径")
    parser.add_argument(
        "--mode",
        choices=["frame", "sticker"],
        default="frame",
        help="处理模式: frame=底部边框, sticker=内部贴纸 (默认: frame)",
    )
    parser.add_argument(
        "--text",
        required=True,
        help="配文内容（支持中文和 Emoji）",
    )
    parser.add_argument(
        "--font",
        help="自定义字体文件路径",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=32,
        help="字体大小 (默认: 32)",
    )
    parser.add_argument(
        "--bg-color",
        default=None,
        help="背景颜色 (默认: frame=white, sticker=#FFE4B5)",
    )
    parser.add_argument(
        "--text-color",
        default=None,
        help="文字颜色 (默认: frame=black, sticker=#333333)",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=20,
        help="内边距 (默认: 20)",
    )

    # 贴纸模式专用参数
    sticker_group = parser.add_argument_group("贴纸模式参数")
    sticker_group.add_argument(
        "--position",
        choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
        default="bottom-right",
        help="贴纸位置 (默认: bottom-right)",
    )
    sticker_group.add_argument(
        "--opacity",
        type=int,
        default=230,
        help="背景透明度 0-255 (默认: 230)",
    )
    sticker_group.add_argument(
        "--radius",
        type=int,
        default=10,
        help="圆角半径 (默认: 10)",
    )
    sticker_group.add_argument(
        "--margin",
        type=int,
        default=20,
        help="距边缘距离 (默认: 20)",
    )

    args = parser.parse_args()

    # 查找中文字体
    font_path = find_chinese_font(args.font)

    # 设置默认颜色
    if args.bg_color is None:
        args.bg_color = "white" if args.mode == "frame" else "#FFE4B5"
    if args.text_color is None:
        args.text_color = "black" if args.mode == "frame" else "#333333"

    # 处理图片
    success = process_image(
        input_path=args.input,
        output_path=args.output,
        mode=args.mode,
        text=args.text,
        font=font_path,
        font_size=args.font_size,
        bg_color=args.bg_color,
        text_color=args.text_color,
        padding=args.padding,
        position=args.position,
        opacity=args.opacity,
        radius=args.radius,
        margin=args.margin,
    )

    if success:
        print(f"处理完成: {args.output}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
