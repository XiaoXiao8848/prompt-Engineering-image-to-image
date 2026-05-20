# 产品图生图 · 多场景提示词工程

根据**产品信息**与**参考图（图生图）**，批量生成不同营销/拍摄场景的 **提示词**（每个场景一条），用于 Stable Diffusion、ComfyUI、Midjourney 等图生图工作流。

## 项目结构

```
prompt-engineering/
├── products/                 # 产品配置（名称、材质、卖点、参考图说明）
├── scenes/                   # 场景库（棚拍、家居、户外、节日等）
├── prompts/
│   ├── system/               # 图生图提示词工程师角色
│   ├── templates/            # 直接渲染的 SD 风格模板（无需 API）
│   └── meta/                 # 调用 LLM 扩写场景的元提示词
├── outputs/                  # 生成的场景提示词（gitignore）
├── examples/                 # 完整输入输出样例
├── docs/                     # 图生图最佳实践
├── src/
└── scripts/
    ├── generate_scenes.py    # 核心：一键生成全部场景
    ├── render_prompt.py
    └── run_prompt.py
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API（可选）

仅在使用 **LLM 扩写模式** 时需要。复制 `.env.example` 为 `.env` 并填入 Key。

模板模式（`--mode template`）无需 API，适合本地快速出词。

### 3. 编辑产品配置

在 `products/` 下新建 YAML，参考 `products/skincare_serum.yaml`。

### 4. 生成全部场景提示词

```bash
# 模板模式（默认，离线可用）
python scripts/generate_scenes.py products/skincare_serum.yaml

# 指定场景
python scripts/generate_scenes.py products/skincare_serum.yaml --scenes studio_clean,lifestyle_home

# LLM 扩写模式（更自然、更贴产品）
python scripts/generate_scenes.py products/skincare_serum.yaml --mode llm

# 导出 ComfyUI / SD WebUI 友好 JSON
python scripts/generate_scenes.py products/skincare_serum.yaml --format workflow
```

输出目录：`outputs/<product_id>/`

## 图生图核心原则

1. **产品锚定**：提示词开头必须包含 `lock_tags`，锁定产品外观
2. **只改场景**：背景、光线、道具、氛围可变；产品形状、配色、logo 位置不变
3. **参考图权重**：在 `img2img` 参数中建议 `denoising_strength` 0.35–0.55（场景差异大时偏低）
4. **批量一致性**：同一产品用同一套 `product.lock_tags` 前缀，仅替换 `scene` 块

## 场景一览

| ID | 名称 | 适用 |
|----|------|------|
| studio_clean | 纯白棚拍 | 电商主图、详情首图 |
| lifestyle_home | 家居生活 | 日用品、家电、食品 |
| lifestyle_office | 办公桌面 | 数码、文具、饮品 |
| outdoor_nature | 自然户外 | 运动、户外、环保类 |
| outdoor_urban | 城市街拍 | 时尚、潮牌 |
| luxury_marble | 轻奢大理石 | 美妆、珠宝、高端礼盒 |
| water_splash | 水花动感 | 饮料、护肤、清洁 |
| seasonal_spring | 春日氛围 | 季节营销 |
| seasonal_christmas | 圣诞节日 | 节日礼盒 |
| gift_box | 礼盒包装 | 节庆促销 |
| minimal_desk | 桌面静物 | 小家电、配件 |
| hands_holding | 手持展示 | 美妆、手机、饮品 |

## 许可证

MIT
