<p align="center">
  <a href="README.md">中文</a> | <a href="readme-en.md">English</a>
</p>

# TikTok Product Listing Skill

TikTok Shop product listing Skill. It turns warehouse inventory, images, and product notes into a reviewable `商品上架.xlsx`, then uses the TikTok Shop Open API to upload images, dry-run Create Product payloads, and create draft products.

This Skill is designed for general-purpose agents. It is not tied to Codex, Claude, or OpenClaw. An agent can read `SKILL.md`, `skill.yaml`, and the bundled resources in this directory to execute the same product-listing workflow.

## Scope

**Responsible for:**

- Parsing inventory Excel files and grouping variants by parent product.
- Letting the agent extract size, color, and piece count from Chinese product names.
- Generating English titles and HTML descriptions through an LLM workflow.
- Producing a multi-category `商品上架.xlsx` with TikTok category attribute columns.
- Uploading product images, variant images, and size-chart images to TikTok Shop.
- Reading reviewed templates and generating Create Product payloads.
- Defaulting to dry-run and creating draft products only after explicit confirmation.

**Not responsible for:**

- Bypassing TikTok authorization, permissions, IP allowlists, or platform controls.
- Publishing or activating products without explicit user approval.
- Fabricating compliance answers, materials, origin, functions, or other product facts.
- Replacing human review of titles, descriptions, images, and compliance fields.

## Architecture

```text
raw_inventory.xlsx
  -> tiktok_product_excel_parser.py
  -> product_groups.json
  -> Agent Task A: parse Chinese names into size/color/pcs
  -> Agent Task B: generate English title and HTML description using references/llm-content-template.md
  -> product_groups_enhanced.json
  -> tiktok_product_to_template.py
  -> 商品上架.xlsx
  -> tiktok_product_image_uploader.py
  -> image_uri_map.json
  -> tiktok_product_create.py
  -> dry-run JSON / TikTok draft products
```

## Quick Start

### 1. Install dependencies

```bash
pip install openpyxl requests
```

### 2. Configure environment variables

Copy the environment template and fill in TikTok Shop Open API values:

```bash
cp config/.env.example .env
```

Required values:

```text
TIKTOK_SHOP_APP_KEY=
TIKTOK_SHOP_APP_SECRET=
TIKTOK_SHOP_ACCESS_TOKEN=
TIKTOK_SHOP_REFRESH_TOKEN=
TIKTOK_SHOP_SHOP_REGION=US
```

### 3. Precheck the shop

```bash
python scripts/tiktok_product_listing_precheck.py precheck
```

Confirm:

- The app is authorized for the target shop.
- The current runtime IP is added to the TikTok Partner Center allowlist.
- `shop_cipher` is available.
- A sales `warehouse_id` is available.

### 4. Parse the warehouse inventory

```bash
python scripts/tiktok_product_excel_parser.py warehouse.xlsx --output data/tiktok_product_listing/product_groups.json
```

### 5. Let the agent generate enhanced data

After reading `product_groups.json`, the agent runs two LLM tasks:

- Task A: Chinese product name -> `product_name_cn`, `size`, `color`, `pcs`.
- Task B: Generate English titles and HTML descriptions using [references/llm-content-template.md](references/llm-content-template.md).

Recommended output path:

```text
data/tiktok_product_listing/product_groups_enhanced.json
```

### 6. Generate the listing template

```bash
python scripts/tiktok_product_to_template.py data/tiktok_product_listing/product_groups_enhanced.json --output-dir data/tiktok_product_listing
```

Generated file:

```text
data/tiktok_product_listing/{timestamp}_商品上架.xlsx
```

### 7. Upload images

```bash
python scripts/tiktok_product_image_uploader.py --shop-cipher <shop_cipher> --output data/tiktok_product_listing/image_uri_map.json <image_or_url>...
```

Sources may be local files or URLs. The upload output is used with `--image-uri-map`.

### 8. Dry-run product creation

```bash
python scripts/tiktok_product_create.py data/tiktok_product_listing/{timestamp}_商品上架.xlsx \
  --shop-cipher <shop_cipher> \
  --warehouse-id <warehouse_id> \
  --image-uri-map data/tiktok_product_listing/image_uri_map.json \
  --output data/tiktok_product_listing/create_run.json
```

Dry-run is the default. It does not call Create Product.

### 9. Create draft products

Run this only after the user has reviewed the listing workbook and dry-run output:

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

See [SOP.md](SOP.md) for the Chinese SOP and [sop-en.md](sop-en.md) for the English SOP.

The SOP covers:

- Intake and input checks.
- OAuth, shop, and warehouse prechecks.
- Inventory parsing and LLM enhancement.
- Template generation and human review.
- Image upload and URI mapping.
- Dry-run validation.
- Draft product creation.
- Failure recovery and handoff checklist.

## File Structure

```text
skills/tiktok-product-listing/
├── SKILL.md                         # Agent entrypoint
├── skill.yaml                       # General machine-readable manifest
├── metadata.json                    # Lightweight metadata
├── README.md                        # Chinese README
├── readme-en.md                     # English README
├── SOP.md                           # Chinese SOP
├── sop-en.md                        # English SOP
├── adapters/
│   └── codex.yaml                   # Codex adapter example
├── config/
│   ├── .env.example                 # Environment variable template
│   ├── category_cache.json          # Category hint -> TikTok leaf category cache
│   ├── llm_content_template.md      # Backward-compatible content template path
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

## Scripts

| Script | Responsibility |
|---|---|
| `scripts/tiktok_product_excel_parser.py` | Parse raw inventory Excel and group rows by parent SKU |
| `scripts/tiktok_product_to_template.py` | Convert enhanced JSON to multi-sheet `商品上架.xlsx` |
| `scripts/tiktok_product_image_uploader.py` | Upload local or URL images and return TikTok URI mappings |
| `scripts/tiktok_product_create.py` | Read reviewed templates, assemble payloads, dry-run, or create draft products |
| `scripts/tiktok_product_listing_precheck.py` | Verify shop authorization, prerequisites, and category capability |
| `scripts/tiktok_shop_open_api.py` | TikTok Open API signing, IPv4 behavior, and request helpers |
| `scripts/tiktok_category_attributes.py` | Map template attribute columns to TikTok attribute IDs and value IDs |
| `scripts/tiktok_oauth_callback_server.py` | Capture local OAuth callback codes |

## Input and Output Contract

### Inputs

- Raw warehouse inventory: `.xlsx`.
- Images: local file paths or URLs.
- Optional notes: category, pricing policy, brand notes, compliance notes.
- TikTok Open API credentials: `.env`.

### Intermediate files

```text
data/tiktok_product_listing/product_groups.json
data/tiktok_product_listing/product_groups_enhanced.json
data/tiktok_product_listing/{timestamp}_商品上架.xlsx
data/tiktok_product_listing/image_uri_map.json
data/tiktok_product_listing/create_run.json
```

### Outputs

- Reviewable `商品上架.xlsx`.
- Dry-run payloads and validation report.
- TikTok Shop draft product IDs or API error details.

## Agent Integration

### General agents

1. Read `skill.yaml` for capabilities, dependencies, entrypoints, and script inventory.
2. Read `SKILL.md` for execution rules.
3. Load `references/` only when detailed context is needed.
4. Use `scripts/` for deterministic steps.
5. Put platform-specific wrappers under `adapters/`; do not modify the core Skill for one agent runtime.

### Codex

See:

```text
adapters/codex.yaml
```

### OpenClaw / other agents

Use these stable entrypoints:

- `skill.yaml`
- `SKILL.md`
- `scripts/`
- `references/`
- `config/.env.example`

If a platform-specific launcher is needed, add it as `adapters/<agent>.yaml`.

## Guardrails

- Product creation requires `--create --confirm 上架`.
- Dry-run is the default mode and the required checkpoint before creation.
- `color`, `size`, and other sales attribute values must be English before the template is written.
- The CLI must not silently translate Chinese sales attribute values; non-English values should block creation.
- Titles and descriptions must follow [references/llm-content-template.md](references/llm-content-template.md).
- Compliance fields must not be fabricated. Defaults must be business-approved and shown in the dry-run summary.
- TikTok API secrets, access tokens, and refresh tokens must never be stored in Skill files.

## Verification

Basic smoke test:

```bash
python scripts/tiktok_product_excel_parser.py --help
python scripts/tiktok_product_to_template.py --help
python scripts/tiktok_product_image_uploader.py --help
python scripts/tiktok_product_create.py --help
```

Project-level tests:

```bash
python -m unittest tests.test_tiktok_product_create -v
python -m unittest tests.test_tiktok_shop_open_api -v
python -m unittest tests.test_tiktok_product_listing_precheck -v
```

## Version History

- `1.0.0`: General Skill packaging release. Includes machine-readable manifest, agent-neutral entrypoint, TikTok listing pipeline, automatic attribute mapping, dry-run safety gate, and draft product creation.

## License

MIT License. See the repository root license file.
