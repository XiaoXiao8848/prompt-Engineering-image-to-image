#!/usr/bin/env python3
"""单条提示词调试/渲染工具.

用法:
    # 渲染指定场景的模板
    python scripts/render_prompt.py products/skincare_serum.yaml --scene studio_clean

    # LLM 扩写单条
    python scripts/render_prompt.py products/skincare_serum.yaml --scene studio_clean --mode llm

    # 查看所有可用场景
    python scripts/render_prompt.py --list-scenes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import load_product_config, load_scene_library
from src.prompt_engine import create_engine


load_dotenv()
console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="单条提示词渲染与调试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("product", nargs="?", default="", help="产品配置文件路径（YAML）")
    parser.add_argument(
        "--scene",
        required=False,
        help="场景 ID",
    )
    parser.add_argument(
        "--mode",
        choices=["template", "llm"],
        default="template",
        help="生成模式",
    )
    parser.add_argument(
        "--list-scenes",
        action="store_true",
        help="列出所有可用场景",
    )
    parser.add_argument(
        "--scenes-file",
        default="scenes/scenes.yaml",
        help="场景库文件路径",
    )
    parser.add_argument(
        "--templates-dir",
        default="prompts/templates",
        help="模板目录路径",
    )
    parser.add_argument(
        "--meta-template",
        default="prompts/meta/expand_scene.yaml",
        help="LLM 扩写元提示词模板路径",
    )
    return parser.parse_args()


def list_scenes(scenes_file: Path) -> None:
    """列出所有可用场景."""
    if not scenes_file.exists():
        console.print(f"[red]场景库不存在: {scenes_file}[/red]")
        return

    scenes = load_scene_library(scenes_file)
    console.print("[bold cyan]可用场景列表:[/bold cyan]\n")
    for sid, scene in scenes.items():
        console.print(f"  [green]{sid}[/green] — {scene.name}")
        console.print(f"    {scene.description}\n")


def main() -> int:
    args = parse_args()

    scenes_file = Path(args.scenes_file)

    if args.list_scenes:
        list_scenes(scenes_file)
        return 0

    if not args.product or not args.scene:
        console.print("[red]错误：需要提供产品配置文件和场景 ID[/red]")
        console.print("用法: python scripts/render_prompt.py <product.yaml> --scene <scene_id>")
        return 1

    product_path = Path(args.product)
    if not product_path.exists():
        console.print(f"[red]错误：产品配置文件不存在: {product_path}[/red]")
        return 1

    # 加载配置
    product = load_product_config(product_path)
    scenes = load_scene_library(scenes_file)

    if args.scene not in scenes:
        console.print(f"[red]错误：场景 '{args.scene}' 不存在[/red]")
        console.print(f"可用场景: {', '.join(scenes.keys())}")
        return 1

    scene = scenes[args.scene]

    console.print(f"[blue]产品:[/blue] {product.product_name}")
    console.print(f"[blue]场景:[/blue] {scene.name} ({scene.id})")
    console.print(f"[blue]模式:[/blue] {args.mode}\n")

    # 创建引擎并生成
    try:
        engine = create_engine(
            mode=args.mode,
            product=product,
            templates_dir=Path(args.templates_dir),
            meta_template_path=Path(args.meta_template),
        )
    except RuntimeError as e:
        console.print(f"[red]错误：{e}[/red]")
        return 1

    result = engine.generate(scene)

    # 输出结果
    console.print(Panel(
        result.prompt,
        title=f"[bold green]正向提示词 — {result.scene_name}[/bold green]",
        border_style="green",
    ))

    if result.negative_prompt:
        console.print(Panel(
            result.negative_prompt,
            title=f"[bold yellow]负向提示词[/bold yellow]",
            border_style="yellow",
        ))

    if result.parameters:
        console.print("[bold cyan]推荐参数:[/bold cyan]")
        for k, v in result.parameters.items():
            console.print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
