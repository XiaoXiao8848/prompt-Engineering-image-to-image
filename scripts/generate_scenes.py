#!/usr/bin/env python3
"""核心脚本：一键生成全部场景提示词.

用法:
    # 模板模式（默认，离线可用）
    python scripts/generate_scenes.py products/skincare_serum.yaml

    # 指定场景
    python scripts/generate_scenes.py products/skincare_serum.yaml --scenes studio_clean,lifestyle_home

    # LLM 扩写模式（需要 DeepSeek API Key）
    python scripts/generate_scenes.py products/skincare_serum.yaml --mode llm

    # 导出 ComfyUI / SD WebUI 友好 JSON
    python scripts/generate_scenes.py products/skincare_serum.yaml --format workflow
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# 将项目根目录加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import load_product_config, load_scene_library
from src.models import PromptBatchOutput
from src.prompt_engine import create_engine


load_dotenv()
console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批量生成产品多场景图生图提示词",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s products/skincare_serum.yaml
  %(prog)s products/skincare_serum.yaml --mode llm --scenes studio_clean,lifestyle_home
  %(prog)s products/skincare_serum.yaml --format workflow -o outputs/
        """,
    )
    parser.add_argument("product", help="产品配置文件路径（YAML）")
    parser.add_argument(
        "--mode",
        choices=["template", "llm"],
        default="template",
        help="生成模式：template（默认，离线）或 llm（调用 DeepSeek API）",
    )
    parser.add_argument(
        "--scenes",
        default="",
        help="指定场景 ID，逗号分隔（默认全部）",
    )
    parser.add_argument(
        "--format",
        choices=["json", "workflow"],
        default="json",
        help="输出格式：json（默认）或 workflow（ComfyUI/SD WebUI 兼容）",
    )
    parser.add_argument(
        "-o", "--output",
        default="",
        help="输出目录（默认 outputs/<product_id>/）",
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


def save_json_output(batch: PromptBatchOutput, output_dir: Path, fmt: str) -> None:
    """保存批量结果为 JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if fmt == "workflow":
        # ComfyUI / SD WebUI 兼容格式
        workflow = {
            "product_id": batch.product_id,
            "product_name": batch.product_name,
            "mode": batch.mode,
            "scenes": [
                {
                    "scene_id": p.scene_id,
                    "scene_name": p.scene_name,
                    "positive": p.prompt,
                    "negative": p.negative_prompt,
                    "img2img_params": p.parameters,
                }
                for p in batch.prompts
            ],
        }
        data = workflow
    else:
        data = batch.model_dump(mode="json")

    out_path = output_dir / f"{batch.product_id}_prompts.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    console.print(f"[green]✓[/green] 结果已保存: {out_path}")


def print_summary(batch: PromptBatchOutput) -> None:
    """打印生成结果摘要."""
    table = Table(title=f"生成结果 — {batch.product_name}", show_lines=True)
    table.add_column("场景", style="cyan")
    table.add_column("模式", style="magenta")
    table.add_column("提示词长度", justify="right", style="green")
    table.add_column("负向提示词长度", justify="right", style="yellow")

    for p in batch.prompts:
        table.add_row(
            f"{p.scene_name} ({p.scene_id})",
            p.mode,
            str(len(p.prompt)),
            str(len(p.negative_prompt)),
        )

    console.print(table)
    console.print(f"\n[bold]共生成 {len(batch.prompts)} 条提示词[/bold]")


def main() -> int:
    args = parse_args()

    product_path = Path(args.product)
    if not product_path.exists():
        console.print(f"[red]错误：产品配置文件不存在: {product_path}[/red]")
        return 1

    # 加载产品配置
    console.print(f"[blue]加载产品配置:[/blue] {product_path}")
    product = load_product_config(product_path)

    # 加载场景库
    scenes_file = Path(args.scenes_file)
    if not scenes_file.exists():
        console.print(f"[red]错误：场景库文件不存在: {scenes_file}[/red]")
        return 1

    console.print(f"[blue]加载场景库:[/blue] {scenes_file}")
    scenes = load_scene_library(scenes_file)

    # 确定要生成的场景
    if args.scenes:
        scene_ids = [s.strip() for s in args.scenes.split(",")]
        invalid = [sid for sid in scene_ids if sid not in scenes]
        if invalid:
            console.print(f"[yellow]警告：以下场景不存在，已跳过: {', '.join(invalid)}[/yellow]")
        scene_ids = [sid for sid in scene_ids if sid in scenes]
    else:
        scene_ids = list(scenes.keys())

    console.print(f"[blue]生成模式:[/blue] {args.mode}")
    console.print(f"[blue]场景数量:[/blue] {len(scene_ids)}")

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

    batch = engine.generate_batch(scenes, scene_ids)

    # 输出结果
    print_summary(batch)

    # 保存
    output_dir = Path(args.output) if args.output else Path("outputs") / product.product_id
    save_json_output(batch, output_dir, args.format)

    return 0


if __name__ == "__main__":
    sys.exit(main())
