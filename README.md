<p align="center">
  <a href="README.md">中文</a> | <a href="readme-en.md">English</a>
</p>

# TikTok Product Listing Skill

TikTok Shop 商品上架 Skill。它把仓库清单、图片和商品说明转成可审核的 `商品上架.xlsx`，再通过 TikTok Shop Open API 完成图片上传、payload dry-run 校验和商品发布。

本 Skill 面向通用 Agent 设计，不绑定 Codex、Claude 或 OpenClaw。Agent 只需要读取 `SKILL.md`、`skill.yaml` 和本目录资源，即可按同一套流程执行商品上架任务。

## 能力边界

**负责：**

- 解析仓库清单 Excel，并按父商品聚合变体。
- 由 Agent 完成中文商品名解析、颜色/尺码/件数识别和英文标题描述生成。
- 生成多品类 `商品上架.xlsx`，包含 TikTok 类目属性列。
- 上传商品主图、变体图和尺码表图到 TikTok Shop。
- 读取审核后的模板，生成 Create Product payload。
- 默认 dry-run，只有显式确认后才创建 TikTok 已发布商品。

**不负责：**

- 绕过 TikTok 授权、权限、IP allowlist 或平台风控。
- 在没有用户授权的情况下发布/激活商品。
- 编造合规答案、材质、产地、功能或其他商品事实。
- 替代人工审核商品标题、描述、图片和合规字段。

## 架构

```text
原始仓库清单.xlsx
  -> tiktok_product_excel_parser.py
  -> product_groups.json
  -> Agent Task A: 中文名解析，输出 size/color/pcs
  -> Agent Task B: 按 references/llm-content-template.md 生成英文标题和 HTML 描述
  -> product_groups_enhanced.json
  -> tiktok_product_to_template.py
  -> 商品上架.xlsx
  -> tiktok_product_image_uploader.py
  -> image_uri_map.json
  -> tiktok_product_create.py
  -> dry-run JSON / TikTok published products
```

## 快速开始

### 1. 安装依赖

```bash
pip install openpyxl requests
```

### 2. 配置环境变量

复制环境模板并填写 TikTok Shop Open API 信息：

```bash
cp config/.env.example .env
```

必填项：

```text
TIKTOK_SHOP_APP_KEY=
TIKTOK_SHOP_APP_SECRET=
TIKTOK_SHOP_ACCESS_TOKEN=
TIKTOK_SHOP_REFRESH_TOKEN=
TIKTOK_SHOP_SHOP_REGION=US
```

### 3. 预检店铺

```bash
python scripts/tiktok_product_listing_precheck.py precheck
```

确认事项：

- app 已授权目标店铺。
- 当前运行 IP 已加入 TikTok Partner Center allowlist。
- 已拿到 `shop_cipher`。
- 已查询到销售仓 `warehouse_id`。

### 4. 解析仓库清单

```bash
python scripts/tiktok_product_excel_parser.py 仓库清单.xlsx --output data/tiktok_product_listing/product_groups.json
```

### 5. Agent 生成增强数据

Agent 读取 `product_groups.json` 后执行两类 LLM 任务：

- Task A：中文商品名 -> `product_name_cn`、`size`、`color`、`pcs`。
- Task B：按 [references/llm-content-template.md](references/llm-content-template.md) 生成英文标题和 HTML 描述。

输出建议保存为：

```text
data/tiktok_product_listing/product_groups_enhanced.json
```

### 6. 生成上架模板

```bash
python scripts/tiktok_product_to_template.py data/tiktok_product_listing/product_groups_enhanced.json --output-dir data/tiktok_product_listing
```

生成文件形如：

```text
data/tiktok_product_listing/{timestamp}_商品上架.xlsx
```

### 7. 上传图片

```bash
python scripts/tiktok_product_image_uploader.py --shop-cipher <shop_cipher> --output data/tiktok_product_listing/image_uri_map.json <image_or_url>...
```

图片来源可以是本地路径或 URL。上传结果用于 `--image-uri-map`。

### 8. Dry-run 创建 payload

```bash
python scripts/tiktok_product_create.py data/tiktok_product_listing/{timestamp}_商品上架.xlsx \
  --shop-cipher <shop_cipher> \
  --warehouse-id <warehouse_id> \
  --image-uri-map data/tiktok_product_listing/image_uri_map.json \
  --output data/tiktok_product_listing/create_run.json
```

默认只 dry-run，不会调用 Create Product。

### 9. 创建已发布商品

确认用户已审核 `商品上架.xlsx` 和 dry-run 输出后，才执行：

```bash
python scripts/tiktok_product_create.py data/tiktok_product_listing/{timestamp}_商品上架.xlsx \
  --shop-cipher <shop_cipher> \
  --warehouse-id <warehouse_id> \
  --image-uri-map data/tiktok_product_listing/image_uri_map.json \
  --create \
  --confirm 上架 \
  --output data/tiktok_product_listing/create_run.json
```

## SOP

完整操作流程见 [SOP.md](SOP.md)。英文版见 [sop-en.md](sop-en.md)。

SOP 覆盖：

- 任务接收和输入检查。
- OAuth / 店铺 / 仓库预检。
- 清单解析和 LLM 增强。
- 模板生成和人工审核。
- 图片上传和 URI 映射。
- dry-run 校验。
- 商品发布。
- 失败恢复和交付清单。

## 文件结构

```text
skills/tiktok-product-listing/
├── SKILL.md                         # Agent 使用入口
├── skill.yaml                       # 通用机器可读 manifest
├── metadata.json                    # 轻量元数据
├── README.md                        # 中文说明
├── readme-en.md                     # English README
├── SOP.md                           # 中文 SOP
├── sop-en.md                        # English SOP
├── adapters/
│   └── codex.yaml                   # Codex 适配示例
├── config/
│   ├── .env.example                 # 环境变量模板
│   ├── category_cache.json          # 品类提示到叶子类目 ID 的缓存
│   ├── llm_content_template.md      # 兼容旧路径的内容模板
│   ├── tiktok_standard_category_profiles.md
│   └── 商品上架模板_多品类.xlsx
├── references/
│   ├── category-cache.json
│   ├── category-profiles.md
│   └── llm-content-template.md
└── scripts/
    ├── tiktok_product_excel_parser.py
    ├── tiktok_product_to_template.py
    ├── tiktok_product_image_uploader.py
    ├── tiktok_product_create.py
    ├── tiktok_product_listing_precheck.py
    ├── tiktok_shop_open_api.py
    ├── tiktok_category_attributes.py
    └── tiktok_oauth_callback_server.py
```

## 脚本职责

| 脚本 | 职责 |
|---|---|
| `scripts/tiktok_product_excel_parser.py` | 解析原始仓库 Excel，按父 SKU 分组 |
| `scripts/tiktok_product_to_template.py` | enhanced JSON -> 多 sheet `商品上架.xlsx` |
| `scripts/tiktok_product_image_uploader.py` | 上传本地图片或 URL 图片，输出 TikTok URI 映射 |
| `scripts/tiktok_product_create.py` | 读取审核后的模板，组装 payload，dry-run 或创建已发布商品 |
| `scripts/tiktok_product_listing_precheck.py` | 店铺授权、前置条件和类目能力预检 |
| `scripts/tiktok_shop_open_api.py` | TikTok Open API 签名、IPv4 和请求封装 |
| `scripts/tiktok_category_attributes.py` | 模板属性列到 TikTok 属性 ID / 值 ID 的映射 |
| `scripts/tiktok_oauth_callback_server.py` | 本地 OAuth callback code 捕获 |

## 输入输出契约

### 输入

- 原始仓库清单：`.xlsx`。
- 图片：本地路径或 URL。
- 可选补充信息：商品类目、定价策略、品牌说明、合规说明。
- TikTok Open API 凭据：`.env`。

### 中间产物

```text
data/tiktok_product_listing/product_groups.json
data/tiktok_product_listing/product_groups_enhanced.json
data/tiktok_product_listing/{timestamp}_商品上架.xlsx
data/tiktok_product_listing/image_uri_map.json
data/tiktok_product_listing/create_run.json
```

### 输出

- 审核用 `商品上架.xlsx`。
- dry-run payload 和校验报告。
- TikTok Shop published product IDs 或 API 错误详情。

## Agent 接入方式

### 通用 Agent

1. 读取 `skill.yaml` 获取能力、依赖、入口和脚本清单。
2. 读取 `SKILL.md` 获取执行规则。
3. 只在需要长参考时读取 `references/`。
4. 使用 `scripts/` 执行确定性步骤。
5. 将 Agent 平台专属配置放在 `adapters/`，不要改核心技能。

### Codex

可参考：

```text
adapters/codex.yaml
```

### OpenClaw / 其他 Agent

建议只依赖以下稳定入口：

- `skill.yaml`
- `SKILL.md`
- `scripts/`
- `references/`
- `config/.env.example`

如需平台专用启动器，新增到 `adapters/<agent>.yaml`。

## 关键约束

- 创建商品必须显式传入 `--create --confirm 上架`。
- dry-run 是默认模式，也是正式创建前的强制检查点。
- `color`、`size` 等销售属性必须在写入模板前转成英文。
- CLI 不负责静默翻译中文销售属性；非英文值应阻断。
- 英文标题和描述必须遵循 [references/llm-content-template.md](references/llm-content-template.md)。
- 合规字段不得编造；默认值必须能被业务方接受，且应在 dry-run 摘要中展示。
- TikTok API secret、access token、refresh token 不得写入技能文件。

## 验证

基础 smoke test：

```bash
python scripts/tiktok_product_excel_parser.py --help
python scripts/tiktok_product_to_template.py --help
python scripts/tiktok_product_image_uploader.py --help
python scripts/tiktok_product_create.py --help
```

项目级测试：

```bash
python -m unittest tests.test_tiktok_product_create -v
python -m unittest tests.test_tiktok_shop_open_api -v
python -m unittest tests.test_tiktok_product_listing_precheck -v
```

## 版本记录

- `1.0.0`：通用 Skill 包装版本。包含机器可读 manifest、Agent 无关入口、TikTok 商品上架主链路、属性自动映射、dry-run 安全门和商品发布能力。

## 许可证

MIT License。详见项目根目录许可证文件。
