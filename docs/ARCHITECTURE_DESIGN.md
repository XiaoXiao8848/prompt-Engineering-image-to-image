# Prompt Engineering Image-to-Image — 架构设计文档

> 版本：v1.0  
> 日期：2026-06-02  
> 分支：`architecture-design`  
> 目标：将纯文件系统的 CLI 工具演进为支持多用户、高并发、可扩展的生产级服务架构

---

## 一、现状分析

### 1.1 当前架构

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CLI Scripts   │────▶│  YAML Files  │────▶│  JSON Outputs   │
│ (generate_scenes│     │(products/    │     │ (outputs/)      │
│  render_prompt) │     │ scenes/      │     │                 │
│                 │     │ prompts/)    │     │                 │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  DeepSeek API   │
                       │  (LLM 模式)     │
                       └─────────────────┘
```

### 1.2 核心痛点

| 维度 | 现状问题 | 影响 |
|------|---------|------|
| **存储** | 纯 YAML/JSON 文件存储，无数据库 | 无法支持多用户、历史回溯、数据关联查询 |
| **缓存** | 零缓存，每次重新读文件、重复调 LLM | API 成本高、响应慢、无法承受并发 |
| **并发** | 单线程同步执行 | 批量任务阻塞、无法水平扩展 |
| **服务化** | 纯 CLI 脚本 | 无法提供 Web API、无法集成到工作流 |
| **扩展性** | 场景/模板新增需改文件 | 无法动态管理、无版本控制 |
| **可靠性** | 无任务状态、无重试机制 | LLM 调用失败即丢失、无幂等保证 |
| **安全** | 无用户认证、无权限隔离 | 数据泄露风险、无法商业化 |

---

## 二、架构设计目标

1. **服务化**：提供 RESTful API + Web 管理后台，CLI 作为客户端之一
2. **持久化**：MySQL 存储核心业务数据，支持事务、关联查询、历史追溯
3. **高性能**：Redis 多级缓存（模板缓存、LLM 结果缓存、热点数据缓存）
4. **高并发**：Celery + Redis 异步任务队列处理 LLM 调用，支持水平扩展 Worker
5. **可扩展**：插件化模板引擎、场景 marketplace、多模型支持
6. **可靠性**：任务状态机、失败重试、幂等设计、分布式锁防重复提交
7. **安全性**：JWT 认证、RBAC 权限、API 限流、敏感配置加密

---

## 三、总体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              接入层 (Access Layer)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Web UI     │  │  CLI Client │  │  API 消费者 │  │  ComfyUI/SD WebUI   │ │
│  │  (React)    │  │  (Python)   │  │  (SDK)      │  │  (Webhook Callback) │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          └────────────────┴────────────────┴────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API 网关层 (Gateway)                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Nginx / Traefik                                                     │   │
│  │  ├── 负载均衡                                                        │   │
│  │  ├── 限流 (Rate Limit: 100 req/min/ip, 1000 req/min/user)           │   │
│  │  ├── SSL 终止                                                        │   │
│  │  └── 静态资源托管                                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            应用服务层 (Application)                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application (Uvicorn + Gunicorn)                            │   │
│  │  ┌──────────────┬──────────────┬──────────────┬──────────────────┐   │   │
│  │  │ Auth Router  │ Product API  │ Scene API    │ Template API     │   │   │
│  │  │ - /auth/*    │ - /products/*│ - /scenes/*  │ - /templates/*   │   │   │
│  │  ├──────────────┼──────────────┼──────────────┼──────────────────┤   │   │
│  │  │ Prompt API   │ Batch Job API│ History API  │ Webhook API      │   │   │
│  │  │ - /prompts/* │ - /jobs/*    │ - /history/* │ - /webhooks/*    │   │   │
│  │  └──────────────┴──────────────┴──────────────┴──────────────────┘   │   │
│  │                                                                      │   │
│  │  中间件：JWT Auth │ Request ID │ CORS │ Timeout │ Exception Handler   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
┌───────────────────────┐ ┌─────────────────┐ ┌─────────────────────────────┐
│   缓存层 (Redis)       │ │  任务队列        │ │    持久化层 (MySQL)          │
│  ┌─────────────────┐  │ │  ┌─────────────┐│ │  ┌─────────────────────┐    │
│  │ String Cache    │  │ │  │ Celery      ││ │  │ users               │    │
│  │ - 场景库 (TTL 5m)│  │ │  │ Workers     ││ │  │ products            │    │
│  │ - 模板 (TTL 10m) │  │ │  │             ││ │  │ scenes              │    │
│  ├─────────────────┤  │ │  │ 异步任务：   ││ │  │ scene_categories    │    │
│  │ LLM Result Cache│  │ │  │ • LLM 生成  ││ │  │ templates           │    │
│  │ - product+scene │  │ │  │ • 批量导出  ││ │  │ template_versions   │    │
│  │   hash → result │  │ │  │ • 图片预生成││ │  │ generation_jobs     │    │
│  │   (TTL 24h)     │  │ │  │ • Webhook   ││ │  │ generation_results  │    │
│  ├─────────────────┤  │ │  │   回调      ││ │  │ prompt_histories    │    │
│  │ Distributed Lock│  │ │  └─────────────┘│ │  │ api_keys            │    │
│  │ - 防重复提交    │  │ │        │        │ │  │ rate_limit_logs     │    │
│  │ - 批量任务互斥  │  │ │        ▼        │ │  │ operation_logs      │    │
│  ├─────────────────┤  │ │  ┌─────────────┐│ │  └─────────────────────┘    │
│  │ Rate Limit      │  │ │  │ Redis       ││ │                             │
│  │ - Sliding Window│  │ │  │ (Broker +   ││ │  SQLAlchemy + Alembic       │
│  │   限流计数器    │  │ │  │  Backend)   ││ │  连接池: 10-20              │
│  └─────────────────┘  │ │  └─────────────┘│ │                             │
└───────────────────────┘ └─────────────────┘ └─────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            外部依赖 (External)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ DeepSeek API    │  │ MinIO / S3      │  │ ComfyUI / SD WebUI          │  │
│  │ (LLM Provider)  │  │ (图片/文件存储)  │  │ (图生图执行引擎)             │  │
│  │ 可切换：OpenAI  │  │                 │  │ 通过 Webhook 回调结果        │  │
│  │ Claude / 本地   │  │                 │  │                             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、数据存储设计

### 4.1 MySQL 数据库 Schema

数据库名：`prompt_engine`

#### 4.1.1 用户与认证

```sql
-- 用户表
CREATE TABLE users (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE COMMENT '登录名',
    email           VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash   VARCHAR(255) NOT NULL COMMENT 'bcrypt 哈希',
    display_name    VARCHAR(100) COMMENT '显示名称',
    avatar_url      VARCHAR(500) COMMENT '头像',
    role            ENUM('admin', 'user', 'api') DEFAULT 'user' COMMENT '角色',
    status          ENUM('active', 'inactive', 'banned') DEFAULT 'active',
    quota_daily     INT DEFAULT 100 COMMENT '每日生成配额',
    quota_used_today INT DEFAULT 0 COMMENT '今日已用配额',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    INDEX idx_email (email),
    INDEX idx_status_role (status, role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- API Key 表（支持多 Key、权限细分）
CREATE TABLE api_keys (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    key_hash        VARCHAR(255) NOT NULL UNIQUE COMMENT 'Key 的 SHA256 哈希',
    key_prefix      VARCHAR(16) NOT NULL COMMENT 'Key 前缀，用于展示',
    name            VARCHAR(100) COMMENT 'Key 名称',
    permissions     JSON COMMENT '权限列表 ["prompt:read", "prompt:write", "job:manage"]',
    rate_limit      INT DEFAULT 60 COMMENT '每分钟限制请求数',
    last_used_at    DATETIME(3) COMMENT '最后使用时间',
    expires_at      DATETIME(3) COMMENT '过期时间',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_key_hash (key_hash),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API Key 表';
```

#### 4.1.2 产品与场景

```sql
-- 产品表
CREATE TABLE products (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_uuid    CHAR(36) NOT NULL UNIQUE COMMENT '业务 UUID',
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    product_id      VARCHAR(64) NOT NULL COMMENT '产品标识（如 skincare_serum）',
    product_name    VARCHAR(200) NOT NULL COMMENT '产品名称',
    brand           VARCHAR(100) COMMENT '品牌',
    material        VARCHAR(200) COMMENT '材质',
    shape           VARCHAR(200) COMMENT '形状',
    color           VARCHAR(200) COMMENT '颜色',
    size            VARCHAR(50) COMMENT '尺寸',
    lock_tags       TEXT NOT NULL COMMENT '产品外观锁定标签',
    selling_points  JSON COMMENT '核心卖点列表',
    reference_image JSON COMMENT '参考图说明 {description, angle, lighting}',
    material_keywords JSON COMMENT '材质关键词列表',
    brand_tone      VARCHAR(200) COMMENT '品牌调性',
    status          ENUM('active', 'archived', 'deleted') DEFAULT 'active',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_product (user_id, product_id),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品配置表';

-- 场景分类表
CREATE TABLE scene_categories (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(50) NOT NULL COMMENT '分类名称',
    description     VARCHAR(200) COMMENT '描述',
    sort_order      INT DEFAULT 0 COMMENT '排序',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='场景分类表';

-- 场景定义表
CREATE TABLE scenes (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    scene_uuid      CHAR(36) NOT NULL UNIQUE COMMENT '业务 UUID',
    scene_id        VARCHAR(64) NOT NULL COMMENT '场景标识（如 studio_clean）',
    name            VARCHAR(100) NOT NULL COMMENT '场景名称',
    description     TEXT COMMENT '场景描述',
    lighting        TEXT COMMENT '光线描述',
    background      TEXT COMMENT '背景描述',
    props           JSON COMMENT '道具列表',
    atmosphere      VARCHAR(200) COMMENT '氛围',
    keywords        JSON COMMENT '关键词列表',
    category_id     BIGINT UNSIGNED COMMENT '所属分类',
    is_builtin      BOOLEAN DEFAULT FALSE COMMENT '是否内置场景',
    is_public       BOOLEAN DEFAULT TRUE COMMENT '是否公开',
    created_by      BIGINT UNSIGNED COMMENT '创建者（NULL 为系统内置）',
    status          ENUM('active', 'inactive', 'deleted') DEFAULT 'active',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    FOREIGN KEY (category_id) REFERENCES scene_categories(id),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY uk_scene_id (scene_id),
    INDEX idx_category (category_id),
    INDEX idx_status_public (status, is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='场景定义表';
```

#### 4.1.3 模板系统

```sql
-- 模板表
CREATE TABLE templates (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_uuid   CHAR(36) NOT NULL UNIQUE COMMENT '业务 UUID',
    scene_id        BIGINT UNSIGNED NOT NULL COMMENT '关联场景',
    name            VARCHAR(100) NOT NULL COMMENT '模板名称',
    template_type   ENUM('system', 'positive', 'negative', 'meta') NOT NULL COMMENT '模板类型',
    content         TEXT NOT NULL COMMENT '模板内容（Jinja2）',
    variables       JSON COMMENT '所需变量列表',
    is_default      BOOLEAN DEFAULT FALSE COMMENT '是否默认模板',
    created_by      BIGINT UNSIGNED COMMENT '创建者',
    status          ENUM('active', 'inactive', 'deleted') DEFAULT 'active',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_scene_type (scene_id, template_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提示词模板表';

-- 模板版本历史表
CREATE TABLE template_versions (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_id     BIGINT UNSIGNED NOT NULL COMMENT '关联模板',
    version         INT NOT NULL COMMENT '版本号',
    content         TEXT NOT NULL COMMENT '该版本内容',
    changed_by      BIGINT UNSIGNED COMMENT '修改者',
    change_note     VARCHAR(500) COMMENT '变更说明',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    UNIQUE KEY uk_template_version (template_id, version),
    INDEX idx_template_id (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板版本历史';
```

#### 4.1.4 生成任务与结果

```sql
-- 生成任务表（支持批量任务）
CREATE TABLE generation_jobs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    job_uuid        CHAR(36) NOT NULL UNIQUE COMMENT '任务 UUID',
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '提交用户',
    product_id      BIGINT UNSIGNED NOT NULL COMMENT '关联产品',
    mode            ENUM('template', 'llm') NOT NULL COMMENT '生成模式',
    scene_ids       JSON NOT NULL COMMENT '目标场景 ID 列表',
    status          ENUM('pending', 'queued', 'running', 'partial', 'completed', 'failed', 'cancelled')
                        DEFAULT 'pending' COMMENT '任务状态',
    total_tasks     INT NOT NULL DEFAULT 0 COMMENT '总子任务数',
    completed_tasks INT NOT NULL DEFAULT 0 COMMENT '已完成子任务数',
    failed_tasks    INT NOT NULL DEFAULT 0 COMMENT '失败子任务数',
    llm_model       VARCHAR(50) COMMENT '使用的 LLM 模型',
    llm_temperature DECIMAL(3,2) DEFAULT 0.70 COMMENT '温度参数',
    parameters      JSON COMMENT '额外参数',
    webhook_url     VARCHAR(500) COMMENT '完成回调 URL',
    started_at      DATETIME(3) COMMENT '开始时间',
    completed_at    DATETIME(3) COMMENT '完成时间',
    error_message   TEXT COMMENT '错误信息',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_status_created (status, created_at),
    INDEX idx_job_uuid (job_uuid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生成任务表';

-- 生成结果表（原子级）
CREATE TABLE generation_results (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    result_uuid     CHAR(36) NOT NULL UNIQUE COMMENT '结果 UUID',
    job_id          BIGINT UNSIGNED NOT NULL COMMENT '所属任务',
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    product_id      BIGINT UNSIGNED NOT NULL COMMENT '关联产品',
    scene_id        BIGINT UNSIGNED NOT NULL COMMENT '关联场景',
    status          ENUM('pending', 'running', 'success', 'failed', 'cached')
                        DEFAULT 'pending' COMMENT '子任务状态',
    mode            ENUM('template', 'llm') NOT NULL,
    prompt          TEXT COMMENT '正向提示词',
    negative_prompt TEXT COMMENT '负向提示词',
    parameters      JSON COMMENT '推荐参数',
    llm_raw_response TEXT COMMENT 'LLM 原始响应（调试用）',
    cache_hit       BOOLEAN DEFAULT FALSE COMMENT '是否命中缓存',
    error_message   TEXT COMMENT '错误信息',
    retry_count     INT DEFAULT 0 COMMENT '重试次数',
    started_at      DATETIME(3) COMMENT '开始时间',
    completed_at    DATETIME(3) COMMENT '完成时间',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (job_id) REFERENCES generation_jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE,
    INDEX idx_job (job_id),
    INDEX idx_user_product (user_id, product_id),
    INDEX idx_scene (scene_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生成结果表';

-- 提示词历史表（用于相似推荐、版本对比）
CREATE TABLE prompt_histories (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL COMMENT '所属用户',
    product_id      BIGINT UNSIGNED NOT NULL COMMENT '关联产品',
    scene_id        BIGINT UNSIGNED NOT NULL COMMENT '关联场景',
    prompt_hash     CHAR(64) NOT NULL COMMENT '提示词 SHA256 哈希',
    prompt          TEXT NOT NULL COMMENT '提示词全文',
    negative_prompt TEXT COMMENT '负向提示词',
    parameters      JSON COMMENT '参数',
    generation_count INT DEFAULT 1 COMMENT '被生成次数',
    last_used_at    DATETIME(3) COMMENT '最后使用时间',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE CASCADE,
    UNIQUE KEY uk_prompt_hash (prompt_hash),
    INDEX idx_user_scene (user_id, scene_id),
    INDEX idx_last_used (last_used_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提示词历史去重表';
```

#### 4.1.5 运维与审计

```sql
-- 限流日志表
CREATE TABLE rate_limit_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED COMMENT '用户 ID',
    api_key_id      BIGINT UNSIGNED COMMENT 'API Key ID',
    endpoint        VARCHAR(200) NOT NULL COMMENT '请求端点',
    request_method  VARCHAR(10) NOT NULL,
    client_ip       VARCHAR(45) NOT NULL COMMENT '客户端 IP',
    result          ENUM('allowed', 'blocked') NOT NULL COMMENT '限流结果',
    blocked_reason  VARCHAR(200) COMMENT '拦截原因',
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    INDEX idx_user_time (user_id, created_at),
    INDEX idx_ip_time (client_ip, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='限流日志';

-- 操作审计日志表
CREATE TABLE operation_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED COMMENT '操作用户',
    action          VARCHAR(50) NOT NULL COMMENT '操作类型',
    resource_type   VARCHAR(50) NOT NULL COMMENT '资源类型',
    resource_id     VARCHAR(100) COMMENT '资源 ID',
    details         JSON COMMENT '操作详情',
    client_ip       VARCHAR(45),
    user_agent      VARCHAR(500),
    created_at      DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    INDEX idx_user_action (user_id, action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作审计日志';
```

### 4.2 Redis 缓存设计

#### 4.2.1 Key 命名规范

```
格式: <namespace>:<entity>:<identifier>[:<field>]
```

| Key 模式 | 类型 | TTL | 说明 |
|---------|------|-----|------|
| `pe:scene:{scene_id}` | String | 5 min | 场景定义 JSON |
| `pe:scene:list:{category_id?}` | String | 5 min | 场景列表 JSON |
| `pe:template:{template_uuid}` | String | 10 min | 模板内容 |
| `pe:template:default:{scene_id}:{type}` | String | 10 min | 默认模板 |
| `pe:product:{product_uuid}` | Hash | 10 min | 产品配置字段 |
| `pe:llm:cache:{sha256(product+scene+params)}` | String | 24 h | LLM 生成结果缓存 |
| `pe:job:status:{job_uuid}` | String | 任务周期 + 1h | 任务状态快照 |
| `pe:job:results:{job_uuid}` | List | 任务周期 + 1h | 任务结果 ID 列表 |
| `pe:rate_limit:{user_id}:{endpoint}` | String | 1 min | 滑动窗口限流计数 |
| `pe:rate_limit:api:{key_hash}:{endpoint}` | String | 1 min | API Key 限流计数 |
| `pe:lock:job:{job_uuid}` | String | 5 min | 分布式锁（防重复执行） |
| `pe:lock:product:{product_uuid}` | String | 30 s | 产品编辑锁 |
| `pe:session:{jwt_jti}` | String | JWT exp | 会话黑名单（登出用） |
| `pe:quota:{user_id}:{YYYY-MM-DD}` | String | 24 h | 当日配额计数 |
| `pe:leader:celery_scheduler` | String | 30 s | Celery Beat 主节点锁 |
| `pe:stats:daily:{YYYY-MM-DD}` | Hash | 7 days | 每日统计（生成数、缓存命中率） |

#### 4.2.2 缓存策略

```python
# 1. 读取策略：Cache-Aside（旁路缓存）
async def get_scene(scene_id: str) -> Scene:
    # 先读 Redis
    cache_key = f"pe:scene:{scene_id}"
    cached = await redis.get(cache_key)
    if cached:
        return Scene.parse_raw(cached)

    # 未命中则读 MySQL
    scene = await db.query(Scene).filter(Scene.scene_id == scene_id).first()
    if scene:
        await redis.setex(cache_key, 300, scene.json())  # TTL 5 min
    return scene

# 2. 写入策略：Write-Through + 延迟双删
async def update_scene(scene_id: str, data: dict) -> Scene:
    # 先删缓存
    cache_key = f"pe:scene:{scene_id}"
    await redis.delete(cache_key)

    # 更新数据库
    scene = await db.execute(update(Scene).where(...).values(**data))

    # 再删缓存（延迟双删防止脏读）
    await redis.delete(cache_key)
    return scene

# 3. LLM 结果缓存：基于请求特征哈希
async def get_llm_cache(product: ProductConfig, scene: SceneDefinition,
                        mode: str, model: str, temperature: float) -> Optional[GeneratedPrompt]:
    cache_key = f"pe:llm:cache:{compute_hash(product, scene, mode, model, temperature)}"
    cached = await redis.get(cache_key)
    return GeneratedPrompt.parse_raw(cached) if cached else None

# 4. 批量预热：启动时或定时任务将热点数据写入 Redis
async def warmup_cache():
    # 预热公开场景库
    public_scenes = await db.query(Scene).filter(Scene.is_public == True).all()
    for scene in public_scenes:
        await redis.setex(f"pe:scene:{scene.scene_id}", 300, scene.json())
```

---

## 五、服务层设计

### 5.1 分层架构

```
┌─────────────────────────────────────────────┐
│              Router 层 (路由/校验)            │
│  - 参数校验 (Pydantic)                       │
│  - 依赖注入 (FastAPI Depends)                │
│  - 权限检查 (RBAC)                           │
├─────────────────────────────────────────────┤
│             Service 层 (业务逻辑)             │
│  - 业务规则编排                               │
│  - 事务管理                                   │
│  - 缓存策略调用                               │
├─────────────────────────────────────────────┤
│           Repository 层 (数据访问)            │
│  - SQLAlchemy CRUD 封装                       │
│  - 查询优化/分页                              │
│  - 复杂查询 Builder                           │
├─────────────────────────────────────────────┤
│           Storage 层 (存储抽象)               │
│  - MySQLClient (事务、连接池)                 │
│  - RedisClient (缓存、锁、队列)               │
│  - S3Client (文件/图片存储)                   │
└─────────────────────────────────────────────┘
```

### 5.2 核心 Service 设计

#### 5.2.1 PromptEngineService（提示词引擎服务）

```python
class PromptEngineService:
    """提示词生成核心服务 — 替代原有的 PromptEngine 类"""

    def __init__(
        self,
        template_repo: TemplateRepository,
        result_repo: GenerationResultRepository,
        redis_client: Redis,
        llm_client: LLMClient,
        cache_service: CacheService,
    ):
        ...

    async def generate_single(
        self,
        product: ProductConfig,
        scene: SceneDefinition,
        mode: Literal["template", "llm"],
        use_cache: bool = True,
    ) -> GeneratedPrompt:
        """
        单条生成流程：
        1. 检查配额
        2. 如开启缓存，查询 Redis LLM Cache
        3. 根据 mode 选择 TemplateEngine 或 LLMEngine
        4. 异步保存结果到 MySQL
        5. 写入缓存（LLM 模式）
        """

    async def submit_batch_job(
        self,
        user_id: int,
        product_id: int,
        scene_ids: list[str],
        mode: Literal["template", "llm"],
        webhook_url: Optional[str] = None,
    ) -> GenerationJob:
        """
        提交批量任务流程：
        1. 创建 generation_jobs 记录（status=pending）
        2. 创建 generation_results 子任务记录（每个场景一条）
        3. 发送 Celery 任务到队列
        4. 返回 job_uuid 供轮询
        """

    async def get_job_progress(self, job_uuid: str) -> JobProgress:
        """查询任务进度 — 优先读 Redis 缓存，降级到 MySQL"""
```

#### 5.2.2 JobQueueService（任务队列服务）

```python
# Celery 任务定义
celery_app = Celery("prompt_engine", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def execute_llm_generation(self, result_id: int):
    """Celery 异步执行 LLM 生成"""
    try:
        # 1. 获取分布式锁
        lock_key = f"pe:lock:result:{result_id}"
        if not redis.set(lock_key, self.request.id, nx=True, ex=300):
            return {"status": "skipped", "reason": "already_running"}

        # 2. 更新状态为 running
        db.execute(update(GenerationResult).where(id=result_id).values(status="running", started_at=now()))

        # 3. 加载 product + scene 数据
        result = db.query(GenerationResult).get(result_id)
        product = ...
        scene = ...

        # 4. 调 LLM
        prompt = llm_client.generate(product, scene)

        # 5. 保存结果
        db.execute(update(GenerationResult).where(id=result_id).values(
            status="success",
            prompt=prompt.prompt,
            negative_prompt=prompt.negative_prompt,
            parameters=prompt.parameters,
            completed_at=now(),
        ))

        # 6. 写缓存
        cache_key = compute_cache_key(product, scene)
        redis.setex(cache_key, 86400, prompt.json())

        # 7. 更新父任务进度
        update_parent_job_status(result.job_id)

        return {"status": "success"}

    except LLMRateLimitError as exc:
        # 遇到限流，指数退避重试
        retry_in = (2 ** self.request.retries) * 5
        raise self.retry(exc=exc, countdown=retry_in)

    except Exception as exc:
        # 更新失败状态
        db.execute(update(GenerationResult).where(id=result_id).values(
            status="failed",
            error_message=str(exc),
            retry_count=self.request.retries + 1,
        ))
        raise
```

#### 5.2.3 RateLimitService（限流服务）

```python
class RateLimitService:
    """基于 Redis 滑动窗口的分布式限流"""

    async def is_allowed(
        self,
        user_id: int,
        endpoint: str,
        limit: int = 60,      # 每分钟限制
        window: int = 60,     # 窗口大小（秒）
    ) -> tuple[bool, dict]:
        """
        使用 Redis Sorted Set 实现滑动窗口限流：
        - Key: pe:rate_limit:{user_id}:{endpoint}
        - Score: 请求时间戳（毫秒）
        - Member: 请求唯一 ID
        """
        now_ms = int(time.time() * 1000)
        window_start = now_ms - window * 1000
        key = f"pe:rate_limit:{user_id}:{endpoint}"

        pipe = redis.pipeline()
        # 移除窗口外的旧记录
        pipe.zremrangebyscore(key, 0, window_start)
        # 添加当前请求
        pipe.zadd(key, {str(uuid4()): now_ms})
        # 统计窗口内请求数
        pipe.zcard(key)
        # 设置 Key 过期时间
        pipe.expire(key, window)

        _, _, current_count, _ = await pipe.execute()

        if current_count > limit:
            # 超限，删除刚添加的记录
            await redis.zrem(key, str(uuid4()))
            return False, {
                "limit": limit,
                "current": current_count - 1,
                "reset_at": window_start + window * 1000,
            }

        return True, {
            "limit": limit,
            "remaining": limit - current_count,
            "reset_at": window_start + window * 1000,
        }
```

---

## 六、核心流程设计

### 6.1 单条提示词生成（同步）

```
Client ──▶ POST /api/v1/prompts/generate
              │
              ▼
    ┌─────────────────┐
    │  1. JWT 认证    │
    │  2. 参数校验    │
    │  3. 配额检查    │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ 4. 查 Redis 缓存│◀──── 命中？──▶ 直接返回结果
    │   (LLM Cache)   │      Yes
    └────────┬────────┘       No
             ▼
    ┌─────────────────┐
    │ 5. 加载 Product │
    │    和 Scene     │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ 6. 模式分支     │
    │                 │
    │  template ──────┼──▶ 查 Redis 模板 ──▶ Jinja2 渲染 ──▶ 结果
    │                 │
    │  llm ───────────┼──▶ 同步调 LLM API ──▶ 解析 JSON ──▶ 结果
    │                 │      (超时 30s)
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ 7. 保存到 MySQL │
    │    结果表       │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ 8. LLM 模式写入 │
    │    Redis Cache  │
    └────────┬────────┘
             ▼
         返回响应
```

### 6.2 批量生成任务（异步）

```
Client ──▶ POST /api/v1/jobs/batch
              │
              ▼
    ┌─────────────────┐
    │ 1. 创建 Job 记录 │  status = pending
    │ 2. 创建 Result   │  每条场景一个子任务
    │    子任务记录    │  status = pending
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ 3. 发送 Celery   │
    │    任务到队列    │
    └────────┬────────┘
             ▼
         返回 job_uuid
              │
    ◀─────────┘
Client 轮询 GET /api/v1/jobs/{job_uuid}/progress

         Celery Worker 消费任务
              │
              ▼
    ┌─────────────────┐
    │ 4. 获取分布式锁  │──▶ 锁失败 ──▶ 跳过（防重复）
    │ 5. 更新 running  │
    │ 6. 执行生成      │
    │ 7. 更新 success/ │
    │    failed        │
    │ 8. 写 Redis 缓存 │
    │ 9. 更新 Job 进度 │
    │ 10. Webhook 回调 │
    └─────────────────┘
```

### 6.3 模板渲染流程

```
Client ──▶ POST /api/v1/templates/{id}/render
              │
              ▼
    ┌─────────────────┐
    │ 1. 查 Redis 模板 │◀── 命中 ──▶ 使用缓存
    │    缓存         │   未命中
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ 2. 查 MySQL     │
    │    模板内容     │
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ 3. Jinja2 渲染  │──▶ 变量替换 ──▶ 生成提示词
    │    + 变量校验   │
    └────────┬────────┘
             ▼
         返回渲染结果
```

---

## 七、API 接口设计

### 7.1 认证相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 登录获取 JWT |
| POST | `/api/v1/auth/logout` | 登出（Token 加入黑名单） |
| POST | `/api/v1/auth/refresh` | 刷新 Token |
| GET  | `/api/v1/auth/me` | 获取当前用户信息 |

### 7.2 产品管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/v1/products` | 产品列表（分页） |
| POST | `/api/v1/products` | 创建产品 |
| GET  | `/api/v1/products/{uuid}` | 产品详情 |
| PUT  | `/api/v1/products/{uuid}` | 更新产品 |
| DELETE | `/api/v1/products/{uuid}` | 删除产品（软删除） |

### 7.3 场景管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/v1/scenes` | 场景列表（支持分类筛选） |
| POST | `/api/v1/scenes` | 创建自定义场景 |
| GET  | `/api/v1/scenes/{scene_id}` | 场景详情 |
| PUT  | `/api/v1/scenes/{scene_id}` | 更新场景 |
| DELETE | `/api/v1/scenes/{scene_id}` | 删除场景 |

### 7.4 模板管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/v1/templates` | 模板列表 |
| POST | `/api/v1/templates` | 创建模板 |
| GET  | `/api/v1/templates/{uuid}` | 模板详情 |
| PUT  | `/api/v1/templates/{uuid}` | 更新模板（自动创建版本） |
| POST | `/api/v1/templates/{uuid}/render` | 渲染模板 |
| GET  | `/api/v1/templates/{uuid}/versions` | 版本历史 |
| POST | `/api/v1/templates/{uuid}/versions/{version}/restore` | 回滚版本 |

### 7.5 提示词生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/prompts/generate` | 单条同步生成 |
| POST | `/api/v1/jobs/batch` | 提交批量异步任务 |
| GET  | `/api/v1/jobs/{job_uuid}` | 查询任务详情 |
| GET  | `/api/v1/jobs/{job_uuid}/progress` | 查询任务进度 |
| GET  | `/api/v1/jobs/{job_uuid}/results` | 查询任务结果 |
| POST | `/api/v1/jobs/{job_uuid}/cancel` | 取消任务 |

### 7.6 历史与统计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/v1/history/prompts` | 提示词历史 |
| GET  | `/api/v1/history/jobs` | 任务历史 |
| GET  | `/api/v1/stats/usage` | 使用统计 |
| GET  | `/api/v1/stats/cache` | 缓存命中率 |

---

## 八、部署架构

### 8.1 Docker Compose 本地开发

```yaml
# docker-compose.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+asyncmy://user:pass@mysql:3306/prompt_engine
      - REDIS_URL=redis://redis:6379/0
      - LLM_API_KEY=${DEEPSEEK_API_KEY}
    depends_on:
      - mysql
      - redis

  celery_worker:
    build: .
    command: celery -A src.tasks worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=mysql+asyncmy://user:pass@mysql:3306/prompt_engine
      - REDIS_URL=redis://redis:6379/0
      - LLM_API_KEY=${DEEPSEEK_API_KEY}
    depends_on:
      - mysql
      - redis

  celery_beat:
    build: .
    command: celery -A src.tasks beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: prompt_engine
      MYSQL_USER: user
      MYSQL_PASSWORD: pass
    volumes:
      - mysql_data:/var/lib/mysql
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api

volumes:
  mysql_data:
  redis_data:
```

### 8.2 生产部署（K8s）

```
┌─────────────────────────────────────────┐
│           Ingress (Nginx/ALB)           │
│         SSL + Rate Limit + WAF          │
└─────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌───────┐    ┌──────────┐    ┌──────────┐
│ API   │    │  API     │    │  API     │
│ Pod 1 │    │  Pod 2   │    │  Pod N   │
│ (HPA) │    │  (HPA)   │    │  (HPA)   │
└───┬───┘    └────┬─────┘    └────┬─────┘
    │             │               │
    └─────────────┴───────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌───────┐    ┌──────────┐    ┌──────────┐
│Celery │    │ Celery   │    │ Celery   │
│Worker │    │ Worker   │    │ Beat     │
│Pod 1  │    │ Pod 2    │    │ (定时)   │
└───┬───┘    └────┬─────┘    └────┬─────┘
    │             │               │
    └─────────────┴───────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌───────┐    ┌──────────┐    ┌──────────┐
│ MySQL │    │  Redis   │    │  MinIO   │
│Primary│    │ Cluster  │    │  (S3)    │
│+ Replica    │ Sentinel │    │          │
└───────┘    └──────────┘    └──────────┘
```

### 8.3 环境配置

```python
# src/config.py — 分层配置
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "Prompt Engine"
    DEBUG: bool = False
    ENV: str = "production"  # development / staging / production

    # MySQL
    DATABASE_URL: str = "mysql+asyncmy://user:pass@localhost:3306/prompt_engine"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 50

    # LLM
    LLM_PROVIDER: str = "deepseek"  # deepseek / openai / claude
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 3
    LLM_CACHE_TTL: int = 86400  # 24h

    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE: int = 3600  # 1h
    JWT_REFRESH_TOKEN_EXPIRE: int = 604800  # 7d

    # 限流
    RATE_LIMIT_DEFAULT: int = 60  # 每分钟
    RATE_LIMIT_API_KEY: int = 1000

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TIMEOUT: int = 300  # 5min

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 九、演进路线

### Phase 1：基础服务化（1-2 周）

- [ ] 搭建 FastAPI 项目骨架 + 分层目录
- [ ] 集成 SQLAlchemy 2.0 (async) + Alembic 迁移
- [ ] 集成 Redis (aioredis) + 基础缓存封装
- [ ] 实现用户注册/登录/JWT 认证
- [ ] 实现 Product CRUD API（迁移原有 YAML 功能）
- [ ] 实现 Scene CRUD API
- [ ] 实现 Template CRUD + 渲染 API
- [ ] 保留 CLI 客户端，改为调用 HTTP API

### Phase 2：异步与队列（1-2 周）

- [ ] 集成 Celery + Redis 任务队列
- [ ] 实现批量任务提交 / 进度查询 / 取消
- [ ] 实现 LLM 异步生成 Worker
- [ ] 实现 Webhook 回调机制
- [ ] 实现任务状态机 + 失败重试
- [ ] 实现分布式锁（防重复提交）

### Phase 3：性能与可靠性（1 周）

- [ ] 实现 LLM 结果缓存（Redis）
- [ ] 实现多级缓存预热
- [ ] 实现滑动窗口限流
- [ ] 实现配额系统（每日限制）
- [ ] 接入 Prometheus + Grafana 监控
- [ ] 接入 Sentry 错误追踪

### Phase 4：生产就绪（1 周）

- [ ] Docker Compose 本地部署
- [ ] K8s Helm Charts 生产部署
- [ ] CI/CD 流水线（GitHub Actions）
- [ ] 数据库备份策略
- [ ] 日志聚合（ELK / Loki）
- [ ] API 文档（OpenAPI / Swagger）

### Phase 5：高级功能（未来）

- [ ] 多 LLM Provider 动态切换
- [ ] 场景 Marketplace（社区分享）
- [ ] A/B 测试（模板效果对比）
- [ ] 提示词相似度搜索（向量数据库）
- [ ] 图片生成结果存储 + 预览
- [ ] 与 ComfyUI/SD WebUI 深度集成

---

## 十、目录结构（演进后）

```
prompt-engine-image-to-image/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # FastAPI Depends（认证、数据库）
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py         # 认证路由
│   │       ├── products.py     # 产品路由
│   │       ├── scenes.py       # 场景路由
│   │       ├── templates.py    # 模板路由
│   │       ├── prompts.py      # 提示词生成路由
│   │       ├── jobs.py         # 批量任务路由
│   │       ├── history.py      # 历史记录路由
│   │       └── stats.py        # 统计路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # JWT / 密码哈希
│   │   ├── exceptions.py       # 自定义异常
│   │   └── responses.py        # 统一响应格式
│   ├── models/
│   │   ├── __init__.py
│   │   └── domain/             # SQLAlchemy ORM 模型
│   │       ├── user.py
│   │       ├── product.py
│   │       ├── scene.py
│   │       ├── template.py
│   │       ├── generation.py
│   │       └── log.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py             # Pydantic 基础 Schema
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── scene.py
│   │   ├── template.py
│   │   ├── prompt.py
│   │   └── job.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── scene_service.py
│   │   ├── template_service.py
│   │   ├── prompt_engine_service.py
│   │   ├── job_queue_service.py
│   │   ├── cache_service.py
│   │   └── rate_limit_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py             # 通用 CRUD
│   │   ├── user_repo.py
│   │   ├── product_repo.py
│   │   ├── scene_repo.py
│   │   ├── template_repo.py
│   │   └── generation_repo.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy 会话管理
│   │   ├── redis_client.py     # Redis 客户端封装
│   │   ├── storage.py          # S3/MinIO 存储
│   │   └── llm_client.py       # LLM 客户端封装
│   ├── engine/                 # 提示词引擎（兼容原有逻辑）
│   │   ├── __init__.py
│   │   ├── base.py             # 抽象基类
│   │   ├── template_engine.py  # 模板模式
│   │   └── llm_engine.py       # LLM 扩写模式
│   ├── tasks/                  # Celery 异步任务
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── generation_tasks.py
│   └── utils/
│       ├── __init__.py
│       ├── hash.py             # 哈希工具
│       └── validators.py       # 校验工具
├── migrations/                 # Alembic 数据库迁移
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── scripts/                    # 保留 CLI 工具（改为 API 客户端）
│   ├── generate_scenes.py
│   └── render_prompt.py
├── prompts/                    # 初始模板数据（可导入数据库）
│   ├── system/
│   ├── templates/
│   └── meta/
├── scenes/                     # 初始场景数据（可导入数据库）
│   └── scenes.yaml
├── products/                   # 初始产品数据示例
│   └── skincare_serum.yaml
├── web/                        # Web 前端（未来）
│   └── ...
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── k8s/                        # K8s 部署配置
│   └── helm/
├── docs/
│   ├── ARCHITECTURE_DESIGN.md  # 本文件
│   └── API.md                  # API 文档
├── pyproject.toml
├── alembic.ini
└── .env.example
```

---

## 十一、关键设计决策说明

### 11.1 为什么用 MySQL 而不是 PostgreSQL？

- 团队熟悉度高，国内云厂商支持好
- 事务和 JSON 字段支持已足够（MySQL 8.0）
- 读写分离、主从复制生态成熟
- 如需全文检索，可后期接入 Elasticsearch

### 11.2 为什么 Redis 既当缓存又当队列？

- **缓存**：String/Hash 存热点数据，TTL 自动过期
- **队列**：Redis List / Stream 作为 Celery Broker，轻量可靠
- **限流**：Sorted Set 实现滑动窗口，原子性操作
- **锁**：SET NX EX 实现分布式锁，简单高效
- 避免引入 Kafka/RabbitMQ 等额外中间件，降低运维复杂度

### 11.3 为什么保留 Template + LLM 双模式？

- **Template 模式**：零成本、毫秒级、可控性高，适合批量快速出词
- **LLM 模式**：质量高、自然度好，适合精品场景
- 两种模式并存，由用户根据场景选择

### 11.4 为什么 Job 和 Result 分表？

- Job 表记录任务元信息（进度、状态），数据量小，查询频繁
- Result 表记录原子结果，数据量大，可按时间分表/归档
- 分离后便于独立优化和扩展

### 11.5 为什么引入 API Key 机制？

- 支持程序化调用（CI/CD、ComfyUI 插件）
- 细粒度权限控制（读/写/管理分离）
- 独立限流和审计，不影响主账号

---

## 十二、附录

### 12.1 技术栈汇总

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| Web 框架 | FastAPI | 异步、高性能、自动 OpenAPI 文档 |
| ORM | SQLAlchemy 2.0 (async) | 异步原生支持、类型提示友好 |
| 迁移 | Alembic | 数据库版本管理 |
| 缓存/队列 | Redis 7 | 缓存 + Celery Broker + 限流 |
| 任务队列 | Celery | 异步任务、定时任务、重试机制 |
| 数据库 | MySQL 8.0 | 主从复制、JSON 支持 |
| 认证 | JWT (PyJWT) + bcrypt | 无状态认证、密码安全 |
| 配置 | Pydantic Settings | 类型安全的环境变量管理 |
| 部署 | Docker + K8s | 容器化、编排、弹性伸缩 |
| 监控 | Prometheus + Grafana | 指标采集与可视化 |
| 日志 | structlog + Loki | 结构化日志、集中查询 |

### 12.2 性能目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| Template 生成 P99 | < 50ms | 本地 Jinja2 渲染 |
| LLM 生成 P99 | < 5s | 含网络往返（DeepSeek）|
| API 响应 P99 | < 100ms | 纯数据库查询接口 |
| 并发用户 | 1000+ | 水平扩展 API Pod |
| 缓存命中率 | > 80% | LLM 结果缓存 + 模板缓存 |
| 任务吞吐量 | 100/min | 单 Worker，可水平扩展 |

---

> 本文档作为架构设计分支的基线，后续迭代请在此之上修改并记录变更日志。
