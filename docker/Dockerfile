# ==========================================
# Prompt Engine — 生产环境 Docker 镜像
# ==========================================

FROM python:3.11-slim AS builder

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# 复制依赖配置
COPY pyproject.toml uv.lock ./

# 安装依赖（利用 uv 缓存）
RUN uv sync --frozen --no-install-project --no-dev

# ==========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# 安装运行时必要的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 复制应用代码
COPY src/ ./src/
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY prompts/ ./prompts/
COPY scenes/ ./scenes/
COPY products/ ./products/

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 默认启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
