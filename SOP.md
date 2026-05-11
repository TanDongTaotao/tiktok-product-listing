<p align="center">
  <a href="SOP.md">中文 SOP</a> | <a href="sop-en.md">English SOP</a>
</p>

# TikTok Product Listing SOP

本 SOP 用于指导 Agent 或运营人员从原始仓库清单走到 TikTok Shop 草稿商品创建。执行时优先使用 dry-run，只有在用户明确确认后才创建商品。

## 0. 执行原则

- 先理解输入，再运行脚本。
- 先生成可审核文件，再调用 TikTok API 创建商品。
- 先 dry-run，再创建草稿商品。
- 遇到不确定的类目、合规、材质、功能或图片归属时，停止并让用户确认。
- 不把 token、secret、shop_cipher、warehouse_id 写入 Skill 文档。

## 1. 接收任务

### 输入清单

确认用户提供了以下内容：

- 仓库清单 Excel，例如 `仓库清单.xlsx`。
- 图片来源：Excel 中的 URL、本地图片目录，或两者都有。
- 店铺授权信息：`.env` 或等价环境变量。
- 上架范围：全部商品、指定父 SKU、指定变体，或待 Agent 判断。
- 业务规则：定价、品牌、合规默认值、是否允许使用 Prop 65 默认 No。

### 初始判断

Agent 需要先判断：

- 表格列名是否清楚。
- 中文名是否已经拆分出颜色/尺码，还是需要从商品名中解析。
- 图片是否能按 SKU、父 SKU、颜色、顺序或映射表匹配。
- 是否存在明显不能上架的数据，例如无库存、无图片、缺英文名、类目不明确。

## 2. 环境和店铺预检

### 2.1 配置 `.env`

从模板创建 `.env`：

```bash
cp config/.env.example .env
```

确认至少包含：

```text
TIKTOK_SHOP_APP_KEY=
TIKTOK_SHOP_APP_SECRET=
TIKTOK_SHOP_ACCESS_TOKEN=
TIKTOK_SHOP_REFRESH_TOKEN=
TIKTOK_SHOP_SHOP_REGION=US
```

### 2.2 如需 OAuth 授权，启动 callback server

```bash
python scripts/tiktok_oauth_callback_server.py --port 3000 --output data/tiktok_oauth_callback.json
```

将 TikTok Partner Center callback URL 配置为：

```text
http://<host>:3000/auth/tiktok/callback
```

### 2.3 执行预检

```bash
python scripts/tiktok_product_listing_precheck.py precheck
```

通过标准：

- 能获取授权店铺。
- 能拿到目标店铺 `shop_cipher`。
- IP allowlist 不报错。
- 能查询 listing prerequisites 或类目信息。
- 能拿到销售仓 `warehouse_id`。

如果返回 `code 36009033`，通常表示当前 IP 未加入 allowlist。

## 3. 解析仓库清单

运行：

```bash
python scripts/tiktok_product_excel_parser.py 仓库清单.xlsx --output data/tiktok_product_listing/product_groups.json
```

检查输出：

- 是否按父 SKU 正确分组。
- 子 SKU 数量是否和原始表一致。
- 库存、价格、重量、图片字段是否被保留。
- 下架或无库存商品是否按业务规则剔除或标记。

## 4. Agent LLM 增强

### 4.1 Task A：中文名解析

对每个变体输出：

```json
{
  "product_name_cn": "纯色圆领长袖连衣裙",
  "size": "XL",
  "color": "Black",
  "pcs": 1
}
```

规则：

- `size` 使用英文标准值，例如 `S`、`M`、`L`、`XL`、`2XL`、`One Size`。
- `color` 必须是英文。
- 颜色代码如 `113#` 只作为内部参考，不直接写入销售属性。
- 多色使用 `+` 或 `/` 连接，例如 `Black + White`。

### 4.2 Task B：英文标题和描述

必须读取并遵循：

```text
references/llm-content-template.md
```

输出要求：

- 标题为英文，pipe-separated SEO 结构。
- 描述为英文 HTML。
- 不残留中文字符。
- 不编造面料、功能、产地、适用场景。

### 4.3 保存增强数据

推荐保存为：

```text
data/tiktok_product_listing/product_groups_enhanced.json
```

检查字段：

- `title_en`
- `description_en`
- `size`
- `color`
- `pcs`
- `category_hint`
- `main_images` 或对应图片字段
- 价格、库存、包裹尺寸和重量

## 5. 生成 `商品上架.xlsx`

运行：

```bash
python scripts/tiktok_product_to_template.py data/tiktok_product_listing/product_groups_enhanced.json --output-dir data/tiktok_product_listing
```

检查生成的 Excel：

- 每个 sheet 对应正确品类。
- 每个父商品和变体都存在。
- 英文标题和英文描述完整。
- `叶子类目ID` 或 `品类提示` 合理。
- 类目属性列已生成，例如材质、季节、风格、图案等。
- `颜色` 和 `尺码` 为英文。

## 6. 人工审核门

在上传图片或创建商品前，让用户审核：

- 商品是否应该上架。
- 标题和描述是否准确。
- 图片归属是否正确。
- 类目和属性是否符合商品。
- 价格、库存、重量、尺寸是否可接受。
- 合规字段是否可以使用默认值。

用户未审核前，不进入创建阶段。

## 7. 上传图片

收集需要上传的图片来源：

- `父商品图片`
- `变体图`
- `尺码表图片`

运行：

```bash
python scripts/tiktok_product_image_uploader.py \
  --shop-cipher <shop_cipher> \
  --output data/tiktok_product_listing/image_uri_map.json \
  <image_or_url>...
```

检查：

- 每个图片来源都有 TikTok URI。
- 失败图片有错误信息。
- 变体图只绑定视觉维度，优先 Color，其次 Size，再其次 PCS。
- 主图是商品级图片，不要误用成某个尺码的图片。

## 8. Dry-run 创建 payload

运行：

```bash
python scripts/tiktok_product_create.py data/tiktok_product_listing/{timestamp}_商品上架.xlsx \
  --shop-cipher <shop_cipher> \
  --warehouse-id <warehouse_id> \
  --image-uri-map data/tiktok_product_listing/image_uri_map.json \
  --output data/tiktok_product_listing/create_run.json
```

可选筛选：

```bash
--parent-sku <parent_sku>
--variant-color Black
--variant-size M
--manifest data/tiktok_product_listing/selection.json
```

检查 `create_run.json`：

- `mode` 是 `dry_run`。
- 每个商品 `status` 是 `ready` 或 `blocked`。
- `validation_errors` 为空才允许创建。
- payload 中 `main_images`、`skus`、`inventory`、`sales_attributes`、`product_attributes` 格式正确。
- category 是 TikTok 叶子类目。
- 不包含明文 secret 或 token。

## 9. 用户确认创建

向用户展示 dry-run 摘要：

- 商品数量和父 SKU。
- 每个商品的类目、价格、库存、图片数量。
- 合规字段和默认值。
- blocked 商品和错误原因。

只有当用户明确确认创建草稿商品时，才进入下一步。推荐确认词为：

```text
上架
```

## 10. 创建 TikTok 草稿商品

运行：

```bash
python scripts/tiktok_product_create.py data/tiktok_product_listing/{timestamp}_商品上架.xlsx \
  --shop-cipher <shop_cipher> \
  --warehouse-id <warehouse_id> \
  --image-uri-map data/tiktok_product_listing/image_uri_map.json \
  --create \
  --confirm 上架 \
  --output data/tiktok_product_listing/create_run.json
```

检查输出：

- `mode` 是 `create`。
- 成功项包含 TikTok `product_id`。
- 失败项保留 API 错误码和消息。
- blocked 商品没有调用 Create Product。

## 11. 交付结果

向用户交付：

- `商品上架.xlsx` 文件位置。
- `image_uri_map.json` 文件位置。
- `create_run.json` 文件位置。
- 成功创建的 draft product IDs。
- 失败商品列表和下一步建议。

## 12. 失败恢复

| 问题 | 处理 |
|---|---|
| IP allowlist 错误 | 将当前出口 IP 加入 TikTok Partner Center allowlist |
| 缺 `shop_cipher` | 重新跑 precheck 或授权流程 |
| 缺 `warehouse_id` | 查询销售仓，避免使用退货仓 |
| 中文颜色被阻断 | 回到增强 JSON，把颜色翻译成英文后重新生成模板 |
| 类目不是叶子类目 | 更新 `category_cache.json` 或让 recommend API 返回 leaf category |
| 属性值匹配失败 | 查询 TikTok 属性值，修正为精确 API 名称 |
| 图片上传失败 | 检查 URL 可访问性、本地路径、图片格式和大小 |
| Create Product API 失败 | 根据 `create_run.json` 中的 API code/message 修正模板或配置 |

## 13. 完成标准

任务完成需满足：

- 用户审核过 `商品上架.xlsx`。
- dry-run 没有未处理的 critical validation error。
- 仅用户确认的商品被创建。
- 创建结果和失败原因已保存。
- 没有 secret 被写入输出文档。
