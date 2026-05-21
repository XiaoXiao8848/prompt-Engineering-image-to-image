# 产品图生图 · 多场景提示词工程

基于 **LangChain 提示词模板**，根据**产品信息**与**参考图（图生图）**，批量生成不同营销/拍摄场景的 **Stable Diffusion 提示词**（每个场景一条），支持模板离线渲染和 LLM 智能扩写两种模式。

## 技术栈

- **LangChain** — `PromptTemplate`（模板渲染）+ `ChatPromptTemplate`（LLM 扩写）
- **DeepSeek Chat** — LLM 扩写模式（兼容 OpenAI 格式）
- **Pydantic** — 产品/场景/生成结果数据模型
- **PyYAML** — 配置与模板管理
- **Rich** — 终端表格与彩色输出
- **pytest** — 单元测试（45 个测试用例）
- **uv** — Python 包管理与虚拟环境

## 项目结构

```
yc_prompt_eg/
├── products/                 # 产品配置（YAML）
│   └── skincare_serum.yaml
├── scenes/                   # 场景定义库（YAML）
│   └── scenes.yaml
├── prompts/
│   ├── system/               # 系统角色 PromptTemplate
│   │   └── img2img_engineer.yaml
│   ├── templates/            # 场景 PromptTemplate（5个）
│   │   ├── studio_clean.yaml
│   │   ├── lifestyle_home.yaml
│   │   ├── luxury_marble.yaml
│   │   ├── water_splash.yaml
│   │   └── outdoor_nature.yaml
│   └── meta/                 # LLM 扩写 ChatPromptTemplate
│       └── expand_scene.yaml
├── outputs/                  # 生成结果（gitignore）
├── examples/                 # 输入输出样例
├── docs/                     # 最佳实践文档
├── src/
│   ├── models.py             # Pydantic 数据模型
│   ├── loader.py             # YAML 加载工具
│   └── prompt_engine.py      # LangChain 核心引擎
├── scripts/
│   ├── generate_scenes.py    # 批量生成入口
│   └── render_prompt.py      # 单条调试工具
├── tests/                    # 单元测试（45个）
├── pyproject.toml            # uv 依赖配置
└── .env.example              # API Key 模板
```

## 快速开始

### 1. 安装依赖

使用 [uv](https://docs.astral.sh/uv/)（推荐）：

```bash
uv sync
```

或传统方式：

```bash
pip install -e .
```

### 2. 配置 API（LLM 模式需要）

```bash
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

模板模式（`--mode template`）**无需 API**，适合本地快速出词。

### 3. 编辑产品配置

在 `products/` 下新建 YAML，参考 `products/skincare_serum.yaml`：

```yaml
product_id: skincare_serum
product_name: 焕颜修护精华液
material: 磨砂玻璃
color: 琥珀色
lock_tags: "amber glass dropper bottle, frosted texture, gold cap"
selling_points:
  - 深层修护
  - 提亮肤色
```

### 4. 生成提示词

```bash
# 模板模式（默认，离线可用）
uv run python scripts/generate_scenes.py products/skincare_serum.yaml

# 指定场景
uv run python scripts/generate_scenes.py products/skincare_serum.yaml --scenes studio_clean,lifestyle_home

# LLM 扩写模式（DeepSeek，更自然）
uv run python scripts/generate_scenes.py products/skincare_serum.yaml --mode llm

# 导出 ComfyUI / SD WebUI 兼容 JSON
uv run python scripts/generate_scenes.py products/skincare_serum.yaml --format workflow
```

输出目录：`outputs/<product_id>/`

### 5. 单条调试

```bash
uv run python scripts/render_prompt.py products/skincare_serum.yaml --scene water_splash
```

## 运行测试

```bash
# 全部测试
uv run pytest tests/ -v

# 指定模块
uv run pytest tests/test_prompt_engine.py -v
```

## 图生图核心原则

1. **产品锚定**：提示词开头必须包含 `lock_tags`，锁定产品外观
2. **只改场景**：背景、光线、道具、氛围可变；产品形状、配色、logo 位置不变
3. **参考图权重**：`img2img` 建议 `denoising_strength` 0.35–0.55（场景差异大时偏低）
4. **批量一致性**：同一产品用同一套 `lock_tags` 前缀，仅替换场景块

## 已实现的场景（5个）

| ID | 名称 | 适用 | 状态 |
|----|------|------|------|
| `studio_clean` | 纯白棚拍 | 电商主图 | ✅ |
| `lifestyle_home` | 家居生活 | 日用品、食品 | ✅ |
| `luxury_marble` | 轻奢大理石 | 美妆、珠宝 | ✅ |
| `water_splash` | 水花动感 | 饮料、护肤 | ✅ |
| `outdoor_nature` | 自然户外 | 运动、环保 | ✅ |

> 更多场景（办公桌面、城市街拍、节日礼盒等）可按 `prompts/templates/*.yaml` 格式扩展。

## 两种生成模式对比

| 特性 | 模板模式 (`template`) | LLM 扩写模式 (`llm`) |
|------|----------------------|----------------------|
| 依赖 | 无需 API | 需要 DeepSeek API Key |
| 速度 | 毫秒级 | 秒级（API 调用） |
| 可控性 | 高（模板固定） | 高（系统提示约束） |
| 自然度 | 结构化 | 更自然流畅 |
| 适用 | 批量快速出词 | 追求文案质量 |

## 许可证

MIT
