<p align="center">
  <a href="SOP.md">中文 SOP</a> | <a href="sop-en.md">English SOP</a>
</p>

# TikTok Product Listing SOP

This SOP guides an agent or operator from raw warehouse inventory to TikTok Shop published product creation. Always dry-run first. Create products only after explicit user confirmation.

## 0. Operating Principles

- Understand the input before running scripts.
- Generate reviewable files before calling TikTok product creation APIs.
- Dry-run before creating published products.
- Stop and ask the user when category, compliance, material, function, or image ownership is uncertain.
- Do not store tokens, secrets, shop cipher values, or warehouse IDs in Skill documents.

## 1. Intake

### Required inputs

Confirm the user provided:

- Warehouse inventory Excel, for example `warehouse.xlsx`.
- Image sources: URLs in Excel, a local image directory, or both.
- Shop authorization values: `.env` or equivalent environment variables.
- Listing scope: all products, selected parent SKUs, selected variants, or agent-determined scope.
- Business rules: pricing, brand, compliance defaults, and whether Prop 65 default "No" is allowed.

### Initial assessment

The agent must determine:

- Whether table columns are clear.
- Whether Chinese product names already contain separate color/size fields or require parsing.
- Whether images can be matched by SKU, parent SKU, color, sequence, or a mapping table.
- Whether any obvious blockers exist, such as no stock, no image, missing English text, or unclear category.

## 2. Environment and Shop Precheck

### 2.1 Configure `.env`

Create `.env` from the template:

```bash
cp config/.env.example .env
```

Confirm at least:

```text
TIKTOK_SHOP_APP_KEY=
TIKTOK_SHOP_APP_SECRET=
TIKTOK_SHOP_ACCESS_TOKEN=
TIKTOK_SHOP_REFRESH_TOKEN=
TIKTOK_SHOP_SHOP_REGION=US
```

### 2.2 Start the OAuth callback server if needed

```bash
python scripts/tiktok_oauth_callback_server.py --port 3000 --output data/tiktok_oauth_callback.json
```

Configure the TikTok Partner Center callback URL as:

```text
http://<host>:3000/auth/tiktok/callback
```

### 2.3 Run precheck

```bash
python scripts/tiktok_product_listing_precheck.py precheck
```

Pass criteria:

- Authorized shop can be fetched.
- Target `shop_cipher` is available.
- IP allowlist does not block requests.
- Listing prerequisites or category info can be queried.
- Sales `warehouse_id` is available.

If TikTok returns `code 36009033`, the current IP is usually not in the allowlist.

## 3. Parse Warehouse Inventory

Run:

```bash
python scripts/tiktok_product_excel_parser.py warehouse.xlsx --output data/tiktok_product_listing/product_groups.json
```

Check:

- Rows are grouped by parent SKU correctly.
- Variant count matches the source table.
- Stock, price, weight, and image fields are preserved.
- Inactive or out-of-stock products are filtered or marked according to business rules.

## 4. Agent LLM Enhancement

### 4.1 Task A: Chinese name parsing

For each variant, output:

```json
{
  "product_name_cn": "纯色圆领长袖连衣裙",
  "size": "XL",
  "color": "Black",
  "pcs": 1
}
```

Rules:

- `size` uses English standard values such as `S`, `M`, `L`, `XL`, `2XL`, `One Size`.
- `color` must be English.
- Color codes such as `113#` are internal references and must not be written as sales attributes.
- Multi-color values may use `+` or `/`, for example `Black + White`.

### 4.2 Task B: English title and description

The agent must read and follow:

```text
references/llm-content-template.md
```

Output requirements:

- Title is English and follows a pipe-separated SEO structure.
- Description is English HTML.
- No Chinese characters remain.
- Do not invent material, function, origin, or use cases.

### 4.3 Save enhanced data

Recommended path:

```text
data/tiktok_product_listing/product_groups_enhanced.json
```

Check fields:

- `title_en`
- `description_en`
- `size`
- `color`
- `pcs`
- `category_hint`
- `main_images` or equivalent image fields
- price, stock, package dimensions, and weight

## 5. Generate `商品上架.xlsx`

Run:

```bash
python scripts/tiktok_product_to_template.py data/tiktok_product_listing/product_groups_enhanced.json --output-dir data/tiktok_product_listing
```

Check the generated Excel:

- Each sheet maps to the correct category.
- Every parent product and variant exists.
- English title and English description are complete.
- `叶子类目ID` or `品类提示` is reasonable.
- Category attribute columns are generated, such as material, season, style, and pattern.
- `颜色` and `尺码` are English.

## 6. Human Review Gate

Before uploading images or creating products, ask the user to review:

- Whether each product should be listed.
- Whether title and description are accurate.
- Whether image ownership and assignment are correct.
- Whether category and attributes fit the product.
- Whether price, stock, weight, and dimensions are acceptable.
- Whether compliance defaults are acceptable.

Do not move to creation before user review.

## 7. Upload Images

Collect image sources:

- `父商品图片`
- `变体图`
- `尺码表图片`

Run:

```bash
python scripts/tiktok_product_image_uploader.py \
  --shop-cipher <shop_cipher> \
  --output data/tiktok_product_listing/image_uri_map.json \
  <image_or_url>...
```

Check:

- Every image source has a TikTok URI.
- Failed images include error details.
- Variant images bind only to the visual dimension: Color first, then Size, then PCS.
- Main images are product-level images and must not be confused with size-specific images.

## 8. Dry-run Create Product Payloads

Run:

```bash
python scripts/tiktok_product_create.py data/tiktok_product_listing/{timestamp}_商品上架.xlsx \
  --shop-cipher <shop_cipher> \
  --warehouse-id <warehouse_id> \
  --image-uri-map data/tiktok_product_listing/image_uri_map.json \
  --output data/tiktok_product_listing/create_run.json
```

Optional filters:

```bash
--parent-sku <parent_sku>
--variant-color Black
--variant-size M
--manifest data/tiktok_product_listing/selection.json
```

Check `create_run.json`:

- `mode` is `dry_run`.
- Each product `status` is `ready` or `blocked`.
- `validation_errors` is empty before creation is allowed.
- Payload fields such as `main_images`, `skus`, `inventory`, `sales_attributes`, and `product_attributes` are correct.
- Category is a TikTok leaf category.
- No secret or token appears in clear text.

## 9. User Confirmation

Show the dry-run summary to the user:

- Product count and parent SKUs.
- Category, price, stock, and image count per product.
- Compliance fields and defaults.
- Blocked products and error reasons.

Proceed only after explicit user confirmation. Recommended confirmation word:

```text
上架
```

## 10. Create TikTok Draft Products

Run:

```bash
python scripts/tiktok_product_create.py data/tiktok_product_listing/{timestamp}_商品上架.xlsx \
  --shop-cipher <shop_cipher> \
  --warehouse-id <warehouse_id> \
  --image-uri-map data/tiktok_product_listing/image_uri_map.json \
  --create \
  --confirm 上架 \
  --output data/tiktok_product_listing/create_run.json
```

Check output:

- `mode` is `create`.
- Successful entries include TikTok `product_id`.
- Failed entries retain API error code and message.
- Blocked products do not call Create Product.

## 11. Handoff

Report back to the user:

- `商品上架.xlsx` path.
- `image_uri_map.json` path.
- `create_run.json` path.
- Successfully created published product IDs.
- Failed products and recommended next actions.

## 12. Failure Recovery

| Issue | Recovery |
|---|---|
| IP allowlist error | Add the current outbound IP to TikTok Partner Center allowlist |
| Missing `shop_cipher` | Re-run precheck or authorization flow |
| Missing `warehouse_id` | Query the sales warehouse, not the return warehouse |
| Chinese color blocked | Fix enhanced JSON with English colors, then regenerate the template |
| Category is not a leaf category | Update `category_cache.json` or use the recommend API leaf result |
| Attribute value mismatch | Query TikTok attribute values and use the exact API name |
| Image upload failed | Check URL reachability, local path, image format, and size |
| Create Product API failed | Fix template or config based on API code/message in `create_run.json` |

## 13. Done Criteria

The task is complete when:

- The user reviewed `商品上架.xlsx`.
- Dry-run has no unresolved critical validation error.
- Only user-confirmed products were created.
- Creation results and failure reasons were saved.
- No secrets were written to output documents.
