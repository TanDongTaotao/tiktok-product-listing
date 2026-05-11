from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import openpyxl


def strip_variant_suffix(sku: str) -> str:
    """Strip the trailing `-数字` variant suffix if present."""
    m = re.search(r"^(.*)-\d+$", sku)
    return m.group(1) if m else sku


def get_catalog_code(row: dict[str, str]) -> str:
    code = row.get("商品编码", "")
    raw = code.rstrip("0")
    return raw if raw else code


def group_by_parent(
    rows: list[dict[str, str]],
    valid_states: set[str] | None = None,
) -> list[dict[str, Any]]:
    if valid_states is None:
        valid_states = {"在售"}

    all_groups: dict[str, dict[str, Any]] = {}

    for row in rows:
        status = (row.get("商品状态") or "").strip()
        if status and status not in valid_states:
            continue
        sku = (row.get("SKU") or row.get("平台SKU") or "").strip()
        if not sku:
            continue
        parent = strip_variant_suffix(sku)
        stock_s = (row.get("库存量") or "0").strip()
        try:
            stock = int(stock_s) if stock_s else 0
        except ValueError:
            stock = 0
        price_s = (row.get("单价") or "0").strip()
        try:
            price_cny = float(price_s) if price_s else 0.0
        except ValueError:
            price_cny = 0.0

        if parent not in all_groups:
            catalog_code = get_catalog_code(row)
            all_groups[parent] = {
                "parent_sku": parent,
                "parent_catalog_code": catalog_code,
                "variants": [],
            }

        all_groups[parent]["variants"].append({
            "sku": sku,
            "name_cn": (row.get("中文名称") or "").strip(),
            "image_url": (row.get("图片URL") or "").strip(),
            "price_cny": price_cny,
            "stock": stock,
            "length_cm": _parse_float(row.get("长")),
            "width_cm": _parse_float(row.get("宽")),
            "height_cm": _parse_float(row.get("高")),
            "weight_g": _parse_float(row.get("商品净重")),
            "declared_name_cn": (row.get("中文报关") or "").strip(),
            "declared_name_en": (row.get("英文报关") or "").strip(),
        })

    groups = list(all_groups.values())
    groups = _filter_zero_stock_groups(groups)
    return groups


def _parse_float(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(value.strip())
    except ValueError:
        return 0.0


def _filter_zero_stock_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        g for g in groups
        if any(v.get("stock", 0) > 0 for v in g["variants"])
        or (g["variants"] and any(v.get("image_url") for v in g["variants"]))
    ]


def parse_xlsx(
    path: str | Path,
    sheet_name: str | None = None,
) -> list[dict[str, str]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active if sheet_name is None else wb[sheet_name]
    except KeyError:
        raise RuntimeError(f"Sheet not found: {sheet_name}")
    ws.reset_dimensions()

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        return []

    header_values = list(rows[1])
    while header_values and header_values[-1] is None:
        header_values.pop()
    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(header_values)]

    results = []
    for data_row in rows[2:]:
        values = list(data_row)
        values += [None] * (len(headers) - len(values))
        row_dict = {}
        for i, header in enumerate(headers):
            row_dict[header] = _format_cell(values[i])
        results.append(row_dict)
    return results


def _format_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return str(value)
    return str(value).strip()


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Parse TikTok inventory xlsx and group by parent SKU.")
    parser.add_argument("xlsx_path", help="Path to the inventory xlsx file")
    parser.add_argument("--sheet", default=None, help="Sheet name (default: active sheet)")
    parser.add_argument("--output", default="data/tiktok_product_listing/product_groups.json")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = parse_xlsx(args.xlsx_path, args.sheet)
    groups = group_by_parent(rows)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(groups, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Parsed {len(rows)} rows, grouped into {len(groups)} parent products")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
