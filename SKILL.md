# TikTok Product Listing Skill

Parse inventory spreadsheets, normalize with LLM, generate listing templates, upload images, and create TikTok Shop published products.

---

## Quick Start

```bash
# 1. Parse warehouse inventory
python scripts/tiktok_product_excel_parser.py <warehouse.xlsx>

# 2. Agent: run Task A + Task B (see workflow) → write enhanced JSON

# 3. Generate listing template
python scripts/tiktok_product_to_template.py <enhanced.json>

# 4. Upload images
python scripts/tiktok_product_image_uploader.py --shop-cipher <cipher> <image_paths...>

# 5. Dry-run
python scripts/tiktok_product_create.py <template.xlsx> --shop-cipher <cipher> --warehouse-id <id>

# 6. Create published products
python scripts/tiktok_product_create.py <template.xlsx> --shop-cipher <cipher> --warehouse-id <id> --create --confirm 上架
```

## Prerequisites

### Environment
Set in `.env`:

```
TIKTOK_SHOP_APP_KEY=
TIKTOK_SHOP_APP_SECRET=
TIKTOK_SHOP_ACCESS_TOKEN=
TIKTOK_SHOP_REFRESH_TOKEN=
```

### Shop Setup
- Register app in TikTok Partner Center
- Add agent IP to IP allowlist
- Run: `python scripts/tiktok_product_listing_precheck.py precheck`
- Get sales warehouse ID: `GET /logistics/202309/warehouses`

## Workflow

### Phase A — Understand Input (Agent LLM)
Map raw columns, assess Chinese name format, define image strategy.

### Phase B — Normalize Data (Agent LLM + Scripts)
```
For each row:
  1. Map columns to standard fields
  2. Task A: Chinese name → size/color/pcs (LLM)
  3. Task B: English title + description — MUST use references/llm-content-template.md
  4. Output category hint
  5. Match images
  → product_groups_enhanced.json
```

### Phase C — Generate Template
```bash
python scripts/tiktok_product_to_template.py <enhanced.json>
```
Produces `{timestamp}_商品上架.xlsx` with per-category attribute columns.

### Phase D — Upload Images
```bash
python scripts/tiktok_product_image_uploader.py --shop-cipher <cipher> <files...>
```

### Phase E — Create Products
```bash
# Dry-run first
python scripts/tiktok_product_create.py <xlsx> --shop-cipher <cipher> --warehouse-id <id>

# Then create
python scripts/tiktok_product_create.py <xlsx> --shop-cipher <cipher> --warehouse-id <id> --create --confirm 上架
```

The CLI reads category-specific columns (材质, 季节, 风格, etc.) from the Excel template and converts them to TikTok API attribute/value IDs automatically.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/tiktok_product_create.py` | Read template, assemble payload, dry-run or create |
| `scripts/tiktok_product_to_template.py` | Enhanced JSON → multi-sheet xlsx |
| `scripts/tiktok_product_image_uploader.py` | Upload images, return TikTok URIs |
| `scripts/tiktok_product_excel_parser.py` | Parse warehouse xlsx, group by parent SKU |
| `scripts/tiktok_product_listing_precheck.py` | Shop auth, prerequisites, category discovery |
| `scripts/tiktok_shop_open_api.py` | Open API signing and request helpers |
| `scripts/tiktok_category_attributes.py` | Column name → TikTok attribute/value ID mapping |

## Key Behaviors

- **Default dry-run**: No product creation without `--create --confirm 上架`.
- **Category resolution**: Excel ID → category cache → TikTok recommend API.
- **Attribute auto-mapping**: Template columns automatically convert to product_attributes with correct value IDs from API cache.
- **English validation**: Non-English sales attribute values are rejected. The CLI does NOT translate them.
- **Output recording**: All payloads and responses saved to run output JSON with secret redaction.

## Configuration

| File | Purpose |
|------|---------|
| `config/category_cache.json` | Category hint → TikTok leaf category ID |
| `config/llm_content_template.md` | **Mandatory** template for LLM title/description generation |
| `references/category-profiles.md` | Full attribute reference per category |

## Verification

```bash
# Smoke test: CLI loads
python scripts/tiktok_product_create.py --help
python scripts/tiktok_product_to_template.py --help

# Parse → template → dry-run (no auth needed)
python scripts/tiktok_product_excel_parser.py <sample.xlsx>
python scripts/tiktok_product_to_template.py <product_groups.json>
python scripts/tiktok_product_create.py <xlsx> --shop-cipher <c> --warehouse-id <w>
```

## Agent Guidelines

- **Title/description**: MUST follow `config/llm_content_template.md`. Pipe-separated SEO titles, HTML with emoji sections.
- **Color/Size**: Must be English before writing to template. CLI rejects non-English values.
- **Compliance**: Prop 65 defaults to "No" unless user specifies otherwise.
- **Category matching**: The Agent should set correct `category_hint` in enhanced JSON. Scripts route by keyword priority.
- **References**: Long docs live in `references/`. Agent-specific configs in `adapters/`.

## Directory Layout

```
SKILL.md              — Entry point
skill.yaml            — Machine-readable manifest
scripts/              — Deterministic Python tools
config/               — Cache, templates, profiles
references/           — Supporting documentation
adapters/             — Agent-specific wrapper configs
```
