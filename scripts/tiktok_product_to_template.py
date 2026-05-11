"""
TikTok Product Listing — Sub-Skill 1: Generate 商品上架.xlsx from enhanced data

Reads product groups JSON (optionally with LLM-parsed fields), maps to
correct category sheet, fills template, writes timestamped xlsx.

LLM-parsed fields (per variant):
  - product_name_cn, size, color, pcs  (Task A)
  - title_en, description_en           (Task B)
If absent, the raw name_cn is used as product_name_cn and size/color/pcs
are left empty for LLM to fill later.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------

CATEGORY_RULES: list[tuple[str, str, list[str]]] = [
    # Most specific first — check these before broad matches
    ("04-内衣文胸", "文胸", [
        "文胸", "内衣",
    ]),
    ("06-睡衣家居", "睡衣", [
        "睡衣", "睡裙", "睡袍", "家居服", "情趣", "性感睡衣",
    ]),
    ("05-内裤", "内裤", [
        "内裤", "三角裤",
    ]),
    ("10-袜子", "袜子", [
        "袜子", "裤袜", "长袜", "短袜", "连裤袜",
    ]),
    ("07-泳衣泳装", "泳衣", [
        "泳衣", "泳装", "比基尼", "沙滩裙", "泳裙",
    ]),
    ("02-上衣T恤", "T恤", [
        "T恤", "t恤", "衬衫", "打底衫", "针织衫",
        "毛衣", "罩衫", "上装", "上衣",
    ]),
    ("08-外套卫衣", "卫衣", [
        "卫衣", "外套", "开衫", "夹克", "风衣", "大衣",
    ]),
    ("09-运动裤", "运动裤", [
        "运动裤", "健身裤", "瑜伽裤",
    ]),
    ("11-运动上衣", "运动上衣", [
        "运动T恤", "速干T恤", "运动上衣",
    ]),
    ("03-裤子短裤", "短裤", [
        "裤子", "短裤",
    ]),
    # Broadest last — full skirt/dress keyword list without single 裙 character
    ("01-连衣裙裙装", "连衣裙", [
        "连衣裙", "吊带裙", "包臀裙", "A字裙", "鱼尾裙",
        "百褶裙", "衬衫裙", "背心裙", "罩衫裙", "开叉裙",
        "连体裙", "半身裙", "套装裙",
    ]),
]

DEFAULT_CATEGORY = "01-连衣裙裙装"
DEFAULT_TIP = "连衣裙"

# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

COMMON_HEADERS = [
    "父商品编号", "子商品SKU", "商品中文名", "商品英文名",
    "英文描述HTML", "品类提示", "叶子类目ID", "采购价CNY",
    "售价USD", "库存数量", "尺码", "颜色", "件数pcs",
    "变体图", "父商品图片", "尺码表图片", "重量g", "长cm", "宽cm", "高cm",
]

SALES_HEADERS: dict[str, list[str]] = {
    "01-连衣裙裙装": ["材质", "季节", "风格", "裙长", "原产国", "袖长", "领型", "闭合方式", "袖型", "图案", "版型", "装饰"],
    "02-上衣T恤":    ["材质", "季节", "风格", "原产国", "袖长", "领型", "闭合方式", "袖型", "图案", "版型", "领型款式"],
    "03-裤子短裤":   ["材质", "季节", "风格", "腰高", "裤长", "原产国", "图案", "版型", "闭合方式", "裤型"],
    "04-内衣文胸":   ["材质", "风格", "原产国", "钢圈类型", "肩带类型", "领型", "闭合方式", "图案", "罩杯类型"],
    "05-内裤":       ["材质", "风格", "原产国", "腰高", "图案", "内裤款式"],
    "06-睡衣家居":   ["材质", "季节", "风格", "原产国", "袖长", "领型", "图案", "闭合方式"],
    "07-泳衣泳装":   ["材质", "季节", "风格", "原产国", "泳衣类型", "运动特性", "图案"],
    "08-外套卫衣":   ["材质", "季节", "风格", "原产国", "袖长", "领型", "闭合方式", "图案", "版型"],
    "09-运动裤":     ["材质", "季节", "风格", "腰高", "原产国", "图案", "版型", "运动特性", "运动类型"],
    "10-袜子":       ["材质", "季节", "风格", "原产国", "袜高", "类型", "图案"],
    "11-运动上衣":   ["材质", "季节", "风格", "原产国", "袖长", "运动特性", "图案", "版型"],
}

ALL_CATEGORIES = [
    "01-连衣裙裙装", "02-上衣T恤", "03-裤子短裤", "04-内衣文胸",
    "05-内裤", "06-睡衣家居", "07-泳衣泳装", "08-外套卫衣",
    "09-运动裤", "10-袜子", "11-运动上衣",
]

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

HF = Font(bold=True, size=11, color="FFFFFF")
HF2 = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
GF = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
EF1 = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
EF2 = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
BD = Border(left=Side("thin"), right=Side("thin"), top=Side("thin"), bottom=Side("thin"))
CT = Alignment(horizontal="center", vertical="center", wrap_text=True)
WR = Alignment(wrap_text=True, vertical="top")

# ---------------------------------------------------------------------------
# Category matching
# ---------------------------------------------------------------------------

def match_category(name_cn: str) -> tuple[str, str]:
    for sheet, hint, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in name_cn:
                return sheet, hint
    return DEFAULT_CATEGORY, DEFAULT_TIP

# ---------------------------------------------------------------------------
# Workbook builder
# ---------------------------------------------------------------------------

def build_workbook(groups: list[dict[str, Any]]) -> openpyxl.Workbook:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    cat_rows: dict[str, list[list[Any]]] = {c: [] for c in ALL_CATEGORIES}

    for g in groups:
        parent = g["parent_sku"]
        variants = g["variants"]
        if not variants:
            continue

        first = variants[0]
        name_cn = first.get("name_cn") or first.get("product_name_cn", "")
        sheet_name, hint = match_category(name_cn)
        sales_hdrs = SALES_HEADERS.get(sheet_name, [])

        # Use LLM-parsed product_name_cn from first variant as the shared product name
        shared_name = first.get("product_name_cn", "") or name_cn

        # --- Image strategy (degradation: Color > Size > PCS) ---
        # Parent product images: user must provide separately (empty for now)
        parent_images_str = ""

        # Choose primary dimension with degradation
        def _primary_key(v: dict) -> str:
            c = v.get("color", "").strip()
            s = v.get("size", "").strip()
            if c:
                return c
            if s and s != "均码":
                return s
            p = str(v.get("pcs", 1))
            return p if p != "1" else "_default"

        variant_images: dict[str, str] = {}
        for v in variants:
            key = _primary_key(v)
            u = v.get("image_url", "").strip()
            if key not in variant_images:
                variant_images[key] = u
            elif u and u not in variant_images[key]:
                variant_images[key] += "," + u

        for v in variants:
            price_cny = v.get("price_cny", 0.0) or 0.0
            stock = v.get("stock", 0) or 0
            img_key = _primary_key(v)

            row = [
                parent,
                v.get("sku", ""),
                v.get("product_name_cn", "") or v.get("name_cn", ""),
                v.get("title_en", ""),
                v.get("description_en", ""),
                hint,
                "",
                str(price_cny) if price_cny else "",
                "",
                str(stock) if stock else "",
                v.get("size", ""),
                v.get("color", ""),
                str(v.get("pcs", 1)),
                variant_images.get(img_key, ""),
                parent_images_str,
                "",   # size chart image
                str(v.get("weight_g", "")) if v.get("weight_g") else "",
                str(v.get("length_cm", "")) if v.get("length_cm") else "",
                str(v.get("width_cm", "")) if v.get("width_cm") else "",
                str(v.get("height_cm", "")) if v.get("height_cm") else "",
            ]
            row += [""] * len(sales_hdrs)
            cat_rows[sheet_name].append(row)

    for cat_name in ALL_CATEGORIES:
        ws = wb.create_sheet(title=cat_name)
        rows_data = cat_rows[cat_name]

        if not rows_data:
            ws.cell(row=1, column=1, value=f"{cat_name}（无数据）")
            continue

        headers = COMMON_HEADERS + SALES_HEADERS.get(cat_name, [])
        col_count = len(headers)

        # Title row
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=col_count)
        tc = ws.cell(row=1, column=1, value=f"{cat_name} - 商品上架模板")
        tc.font = Font(bold=True, size=12, color="FFFFFF")
        tc.fill = GF
        tc.alignment = CT

        # Header row
        for i, h in enumerate(headers):
            c = ws.cell(row=2, column=i + 1, value=h)
            c.font = HF
            c.fill = HF2
            c.alignment = CT
            c.border = BD

        # Data rows
        for ri, row_vals in enumerate(rows_data):
            fill = EF1 if ri % 2 == 0 else EF2
            for ci, val in enumerate(row_vals):
                c = ws.cell(row=3 + ri, column=ci + 1, value=val if val else None)
                c.border = BD
                c.alignment = WR
                c.fill = fill

        # Column widths
        widths = {0: 14, 1: 18, 2: 22, 3: 25, 4: 30, 5: 14, 6: 12, 7: 12, 8: 10,
                  9: 10, 10: 10, 11: 16, 12: 8, 13: 40, 14: 35}
        for ci in range(col_count):
            ws.column_dimensions[get_column_letter(ci + 1)].width = widths.get(ci, 10)

        ws.freeze_panes = "A3"

    return wb

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate 商品上架.xlsx from product groups JSON.")
    parser.add_argument("input_json", nargs="?",
                        default="data/tiktok_product_listing/product_groups.json")
    parser.add_argument("--output-dir", default="data/tiktok_product_listing")
    args = parser.parse_args()

    input_path = Path(args.input_json)
    if not input_path.exists():
        print(f"ERROR: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    groups = json.loads(input_path.read_text(encoding="utf-8"))
    print(f"Read {len(groups)} product groups")

    missing_english = []
    for g in groups:
        for v in g.get("variants", []):
            sku = v.get("sku", "?")
            if not v.get("title_en", "").strip():
                missing_english.append(f"  {g['parent_sku']}/{sku}: missing title_en")
            if not v.get("description_en", "").strip():
                missing_english.append(f"  {g['parent_sku']}/{sku}: missing description_en")
    if missing_english:
        print("ERROR: Some variants are missing required English fields (title_en / description_en):",
              file=sys.stderr)
        for line in missing_english:
            print(line, file=sys.stderr)
        print("Run Task B (LLM Chinese → English translation) first before generating the template.",
              file=sys.stderr)
        sys.exit(1)

    wb = build_workbook(groups)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ts}_商品上架.xlsx"
    wb.save(str(out_path))
    print(f"Saved: {out_path}")

    total = sum(len(g["variants"]) for g in groups)
    print(f"Variants: {total}")
    for s in wb.sheetnames:
        ws = wb[s]
        n = max(0, ws.max_row - 2) if ws.max_row else 0
        if n:
            print(f"  {s}: {n} rows")


if __name__ == "__main__":
    main()
