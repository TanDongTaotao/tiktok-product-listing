from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import openpyxl

from tiktok_shop_open_api import config_from_env, force_ipv4, redact_secrets, request_json

# Common headers always present
COMMON_HEADERS = {
    "父商品编号", "子商品SKU", "商品中文名", "商品英文名",
    "英文描述HTML", "品类提示", "叶子类目ID", "采购价CNY",
    "售价USD", "库存数量", "尺码", "颜色", "件数pcs",
    "变体图", "父商品图片", "尺码表图片", "重量g", "长cm", "宽cm", "高cm",
}


CREATE_PRODUCT_PATH = "/product/202309/products"
CATEGORY_RECOMMEND_PATH = "/product/202309/categories/recommend"
OUTPUT_DIR = Path("data/tiktok_product_listing")
DEFAULT_CATEGORY_CACHE_PATH = Path("skills/tiktok-product-listing/config/category_cache.json")


@dataclass(frozen=True)
class ListingVariant:
    seller_sku: str
    size: str
    color: str
    pcs: str
    sale_price: str
    stock: int | None
    variant_image_sources: tuple[str, ...]
    weight_g: str
    length_cm: str
    width_cm: str
    height_cm: str


@dataclass(frozen=True)
class ListingProduct:
    parent_sku: str
    name_cn: str
    title: str
    description_html: str
    category_hint: str
    category_id: str
    main_image_sources: list[str]
    size_chart_source: str
    variants: list[ListingVariant]
    category_columns: dict[str, str] | None = None


@dataclass(frozen=True)
class Selection:
    parent_skus: set[str] | None = None
    parent_names: set[str] | None = None
    variant_skus: set[str] | None = None
    variant_sizes: set[str] | None = None
    variant_colors: set[str] | None = None
    variant_pcs: set[str] | None = None


def split_sources(value: str) -> list[str]:
    return [part.strip() for part in value.replace("\n", ",").split(",") if part.strip()]


def format_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value).strip()


def parse_int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def rows_from_sheet(ws) -> list[tuple[dict[str, str], dict[str, str]]]:
    """Returns list of (common_fields, category_columns) tuples per row."""
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 3:
        return []
    headers = [format_cell(value) or f"col_{idx}" for idx, value in enumerate(rows[1])]
    if "父商品编号" not in headers or "子商品SKU" not in headers:
        return []

    common_idx = {i for i, h in enumerate(headers) if h in COMMON_HEADERS}
    cat_idx = {i for i, h in enumerate(headers) if h not in COMMON_HEADERS and h.startswith(("父商品编号", "子商品SKU", "商品中文名")) is False}

    parsed = []
    for values in rows[2:]:
        common_row = {}
        cat_row = {}
        for idx, header in enumerate(headers):
            cell_val = format_cell(values[idx] if idx < len(values) else None)
            if header in COMMON_HEADERS:
                common_row[header] = cell_val
            else:
                if cell_val:
                    cat_row[header] = cell_val
        if common_row.get("父商品编号") and common_row.get("子商品SKU"):
            parsed.append((common_row, cat_row))
    return parsed


def parse_listing_workbook(path: str | Path) -> list[ListingProduct]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        groups: dict[str, list[tuple[dict[str, str], dict[str, str]]]] = {}
        for ws in wb.worksheets:
            for common_row, cat_row in rows_from_sheet(ws):
                groups.setdefault(common_row["父商品编号"], []).append((common_row, cat_row))
    finally:
        wb.close()

    products = []
    for parent_sku, grouped in groups.items():
        first_common, first_cat = grouped[0]
        variants = [
            ListingVariant(
                seller_sku=common.get("子商品SKU", ""),
                size=common.get("尺码", ""),
                color=common.get("颜色", ""),
                pcs=common.get("件数pcs", ""),
                sale_price=common.get("售价USD", ""),
                stock=parse_int(common.get("库存数量", "")),
                variant_image_sources=tuple(split_sources(common.get("变体图", ""))),
                weight_g=common.get("重量g", ""),
                length_cm=common.get("长cm", ""),
                width_cm=common.get("宽cm", ""),
                height_cm=common.get("高cm", ""),
            )
            for common, _cat in grouped
        ]
        merged_cat_columns: dict[str, str] = {}
        for _, cat_row in grouped:
            for k, v in cat_row.items():
                if k not in merged_cat_columns:
                    merged_cat_columns[k] = v
        products.append(
            ListingProduct(
                parent_sku=parent_sku,
                name_cn=first_common.get("商品中文名", ""),
                title=first_common.get("商品英文名", ""),
                description_html=first_common.get("英文描述HTML", ""),
                category_hint=first_common.get("品类提示", ""),
                category_id=first_common.get("叶子类目ID", ""),
                main_image_sources=split_sources(first_common.get("父商品图片", "")),
                size_chart_source=first_common.get("尺码表图片", ""),
                variants=variants,
                category_columns=merged_cat_columns,
            )
        )
    return products


def normalize_set(values: list[str] | None) -> set[str] | None:
    cleaned = {value.strip() for value in values or [] if value and value.strip()}
    return cleaned or None


def load_manifest_selection(path: str | Path) -> Selection:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    parent_skus = set()
    variant_skus = set()
    for item in payload.get("parents", []):
        parent_sku = str(item.get("parent_sku", "")).strip()
        if parent_sku:
            parent_skus.add(parent_sku)
        for variant_sku in item.get("variant_skus", []):
            value = str(variant_sku).strip()
            if value:
                variant_skus.add(value)
    return Selection(parent_skus=parent_skus or None, variant_skus=variant_skus or None)


def parent_matches(product: ListingProduct, selection: Selection) -> bool:
    if selection.parent_skus and product.parent_sku not in selection.parent_skus:
        return False
    if selection.parent_names:
        haystack = f"{product.name_cn} {product.title}".lower()
        if not any(name.lower() in haystack for name in selection.parent_names):
            return False
    return True


def variant_matches(variant: ListingVariant, selection: Selection) -> bool:
    if selection.variant_skus and variant.seller_sku not in selection.variant_skus:
        return False
    if selection.variant_sizes and variant.size not in selection.variant_sizes:
        return False
    if selection.variant_colors and variant.color not in selection.variant_colors:
        return False
    if selection.variant_pcs and variant.pcs not in selection.variant_pcs:
        return False
    return True


def select_products(products: list[ListingProduct], selection: Selection) -> list[ListingProduct]:
    selected = []
    for product in products:
        if not parent_matches(product, selection):
            continue
        variants = [variant for variant in product.variants if variant_matches(variant, selection)]
        if variants:
            selected.append(replace(product, variants=variants))
    return selected


def first_variant_image_source(variant: ListingVariant) -> str:
    return variant.variant_image_sources[0] if variant.variant_image_sources else ""


def attribute_values_for_variant(variant: ListingVariant) -> list[dict[str, Any]]:
    attributes = []
    if variant.color:
        attributes.append({"name": "Color", "value_name": variant.color})
    if variant.size:
        attributes.append({"name": "Size", "value_name": variant.size})
    if variant.pcs and variant.pcs != "1":
        attributes.append({"name": "Pieces", "value_name": variant.pcs})
    image_source = first_variant_image_source(variant)
    if image_source and attributes:
        attributes[0]["sku_img"] = {"uri": image_source}
    return attributes


def with_image_uris(payload: dict[str, Any], image_uri_map: dict[str, str]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False)
    for source, uri in image_uri_map.items():
        text = text.replace(json.dumps(source, ensure_ascii=False)[1:-1], uri)
    return json.loads(text)


def format_package_value(value: str) -> str:
    if not value:
        return ""
    try:
        number = float(value)
    except ValueError:
        return value
    if number == int(number):
        return str(int(number))
    return str(number)


def build_product_payload(
    product: ListingProduct,
    shop_cipher: str,
    warehouse_id: str,
    image_uri_map: dict[str, str] | None = None,
    product_attributes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    first_variant = product.variants[0]
    payload: dict[str, Any] = {
        "title": product.title,
        "description": product.description_html,
        "category_id": product.category_id,
        "category_version": "v2",
        "shop_cipher": shop_cipher,
        "main_images": [{"uri": source} for source in product.main_image_sources],
        "package_dimensions": {
            "length": format_package_value(first_variant.length_cm),
            "width": format_package_value(first_variant.width_cm),
            "height": format_package_value(first_variant.height_cm),
            "unit": "CENTIMETER",
        },
        "package_weight": {"value": format_package_value(first_variant.weight_g), "unit": "GRAM"},
        "skus": [
            {
                "seller_sku": variant.seller_sku,
                "price": {"sale_price": variant.sale_price, "currency": "USD"},
                "inventory": [{"quantity": variant.stock, "warehouse_id": warehouse_id}],
                "sales_attributes": attribute_values_for_variant(variant),
            }
            for variant in product.variants
        ],
    }
    if product.size_chart_source:
        payload["size_chart"] = {"image": {"uri": product.size_chart_source}}
    if product_attributes:
        payload["product_attributes"] = product_attributes
    return with_image_uris(payload, image_uri_map or {})


def is_english_value(value: str) -> bool:
    return all(ord(char) < 128 for char in value)


def validate_product(product: ListingProduct, warehouse_id: str) -> list[str]:
    errors = []
    if not product.title:
        errors.append("title is required")
    if not product.description_html:
        errors.append("description_html is required")
    if not product.category_id:
        errors.append("category_id is required")
    if not product.main_image_sources:
        errors.append("at least one main image is required")
    if not warehouse_id:
        errors.append("warehouse_id is required")
    for variant in product.variants:
        prefix = f"variant {variant.seller_sku}: "
        if not variant.seller_sku:
            errors.append(prefix + "seller_sku is required")
        if not variant.sale_price:
            errors.append(prefix + "sale_price is required")
        if variant.stock is None:
            errors.append(prefix + "stock is required")
        if not variant.weight_g:
            errors.append(prefix + "weight_g is required")
        if not variant.length_cm or not variant.width_cm or not variant.height_cm:
            errors.append(prefix + "package dimensions are required")
        attributes = attribute_values_for_variant(variant)
        if not attributes:
            errors.append(prefix + "at least one sales attribute is required")
        for attribute in attributes:
            if not is_english_value(str(attribute.get("value_name") or "")):
                errors.append(prefix + f"sales attribute {attribute.get('name')} must be English")
    return errors


class TikTokProductCreateClient:
    def __init__(self, env_path: str = ".env", ipv4: bool = True):
        if ipv4:
            force_ipv4()
        self.config = config_from_env(env_path)

    def post(self, path: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return request_json(self.config, "POST", path, params=params, body=body)


def recommendation_body(product: ListingProduct) -> dict[str, Any]:
    return {
        "product_title": product.title or product.name_cn or product.parent_sku,
        "description": product.description_html or "<p>Product description pending review.</p>",
        "category_version": "v2",
        "listing_platform": "TIKTOK_SHOP",
    }


def load_category_cache(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    cache_path = Path(path)
    if not cache_path.exists():
        return {}
    return json.loads(cache_path.read_text(encoding="utf-8"))


def save_category_cache(path: str | Path, cache: dict[str, Any]):
    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_category_cache(product: ListingProduct, category_cache: dict[str, Any]) -> ListingProduct:
    if product.category_id:
        return product
    entry = category_cache.get(product.category_hint)
    category_id = str((entry or {}).get("category_id") or "")
    return replace(product, category_id=category_id) if category_id else product


def update_category_cache(
    cache: dict[str, Any],
    product: ListingProduct,
    response: dict[str, Any] | None,
    category_id: str,
) -> bool:
    if not response or not category_id or not product.category_hint:
        return False
    if response.get("code") != 0:
        return False
    data = response.get("data") or {}
    categories = data.get("categories") or []
    category_name = ""
    for category in categories:
        if str(category.get("id") or "") == category_id:
            category_name = str(category.get("name") or category.get("local_name") or "")
            break
    cache[product.category_hint] = {
        "category_id": category_id,
        "category_name": category_name,
        "category_version": "v2",
        "source": "recommend",
    }
    return True


def recommended_category_id(response: dict[str, Any]) -> str:
    data = response.get("data") or {}
    leaf_category_id = str(data.get("leaf_category_id") or "").strip()
    if leaf_category_id:
        return leaf_category_id
    for category in data.get("categories") or []:
        if category.get("is_leaf"):
            return str(category.get("id") or "")
    categories = data.get("categories") or []
    return str(categories[0].get("id") or "") if categories else ""


def apply_category_recommendation(product: ListingProduct, client, shop_cipher: str) -> tuple[ListingProduct, dict[str, Any] | None]:
    if product.category_id:
        return product, None
    response = client.post(CATEGORY_RECOMMEND_PATH, {"shop_cipher": shop_cipher}, recommendation_body(product))
    category_id = recommended_category_id(response)
    return replace(product, category_id=category_id), response


def product_run_entry(
    product: ListingProduct,
    client,
    shop_cipher: str,
    warehouse_id: str,
    image_uri_map: dict[str, str],
    create: bool,
    product_attributes: list[dict[str, Any]],
    category_cache: dict[str, Any] | None = None,
    category_cache_path: str | Path | None = None,
) -> dict[str, Any]:
    cache = category_cache or {}
    product = apply_category_cache(product, cache)
    product, category_response = apply_category_recommendation(product, client, shop_cipher)
    if category_cache_path and category_response is not None and update_category_cache(cache, product, category_response, product.category_id):
        save_category_cache(category_cache_path, cache)
    errors = validate_product(product, warehouse_id)

    # Convert Excel category columns to TikTok product_attributes
    from tiktok_category_attributes import category_columns_to_attributes
    excel_attrs = category_columns_to_attributes(product.category_id, product.category_columns or {})
    # Merge: manually-provided attributes override auto-converted ones
    merged_attrs = excel_attrs
    existing_ids = {a["id"] for a in excel_attrs if "id" in a}
    for attr in product_attributes:
        if attr.get("id") not in existing_ids:
            merged_attrs.append(attr)

    payload = build_product_payload(product, shop_cipher, warehouse_id, image_uri_map, merged_attrs)
    entry: dict[str, Any] = {
        "parent_sku": product.parent_sku,
        "selected_variants": [variant.seller_sku for variant in product.variants],
        "status": "blocked" if errors else "ready",
        "validation_errors": errors,
        "request_payload": payload,
    }
    if category_response is not None:
        entry["category_recommendation_response"] = category_response
    if create and not errors:
        entry["create_response"] = client.post(CREATE_PRODUCT_PATH, {"shop_cipher": shop_cipher}, payload)
    return entry


def run_product_create(
    xlsx_path: str | Path,
    output_path: str | Path,
    client,
    shop_cipher: str,
    warehouse_id: str,
    selection: Selection,
    image_uri_map: dict[str, str] | None = None,
    create: bool = False,
    confirm: str = "",
    product_attributes: list[dict[str, Any]] | None = None,
    category_cache_path: str | Path | None = None,
) -> dict[str, Any]:
    allowed_to_create = create and confirm == "上架"
    run_errors = [] if (not create or allowed_to_create) else ["actual creation requires --create --confirm 上架"]
    mode = "create" if allowed_to_create else "dry_run"
    products = select_products(parse_listing_workbook(xlsx_path), selection)
    cache_path = category_cache_path or DEFAULT_CATEGORY_CACHE_PATH
    category_cache = load_category_cache(cache_path)
    result = {
        "mode": mode,
        "errors": run_errors,
        "products": [
            product_run_entry(
                product=product,
                client=client,
                shop_cipher=shop_cipher,
                warehouse_id=warehouse_id,
                image_uri_map=image_uri_map or {},
                create=allowed_to_create,
                product_attributes=product_attributes or [],
                category_cache=category_cache,
                category_cache_path=cache_path,
            )
            for product in products
        ],
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(redact_secrets(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def build_selection_from_args(args) -> Selection:
    if getattr(args, "manifest", None):
        return load_manifest_selection(args.manifest)
    return Selection(
        parent_skus=normalize_set(getattr(args, "parent_sku", None)),
        parent_names=normalize_set(getattr(args, "parent_name", None)),
        variant_skus=normalize_set(getattr(args, "variant_sku", None)),
        variant_sizes=normalize_set(getattr(args, "variant_size", None)),
        variant_colors=normalize_set(getattr(args, "variant_color", None)),
        variant_pcs=normalize_set(getattr(args, "variant_pcs", None)),
    )


def load_json_file(path: str | Path | None, default):
    if not path:
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_args():
    parser = argparse.ArgumentParser(description="Create TikTok Shop draft products from reviewed 商品上架.xlsx.")
    parser.add_argument("xlsx_path", help="Reviewed 商品上架.xlsx path")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--shop-cipher", required=True)
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--output", default=str(OUTPUT_DIR / "create_run.json"))
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--parent-sku", action="append")
    parser.add_argument("--parent-name", action="append")
    parser.add_argument("--variant-sku", action="append")
    parser.add_argument("--variant-size", action="append")
    parser.add_argument("--variant-color", action="append")
    parser.add_argument("--variant-pcs", action="append")
    parser.add_argument("--manifest")
    parser.add_argument("--image-uri-map", help="JSON mapping from image source to uploaded TikTok image URI")
    parser.add_argument("--product-attributes", help="JSON file containing explicit product_attributes array")
    parser.add_argument("--category-cache", default=str(DEFAULT_CATEGORY_CACHE_PATH), help="JSON cache mapping category hints to TikTok leaf category IDs")
    parser.add_argument("--no-ipv4", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    client = TikTokProductCreateClient(args.env, ipv4=not args.no_ipv4)
    result = run_product_create(
        xlsx_path=args.xlsx_path,
        output_path=args.output,
        client=client,
        shop_cipher=args.shop_cipher,
        warehouse_id=args.warehouse_id,
        selection=build_selection_from_args(args),
        image_uri_map=load_json_file(args.image_uri_map, default={}),
        create=args.create,
        confirm=args.confirm,
        product_attributes=load_json_file(args.product_attributes, default=[]),
        category_cache_path=args.category_cache,
    )
    ready = sum(1 for product in result["products"] if product["status"] == "ready")
    blocked = sum(1 for product in result["products"] if product["status"] == "blocked")
    print(f"Mode: {result['mode']}")
    print(f"Products: {len(result['products'])} total, {ready} ready, {blocked} blocked")
    print(f"Output: {args.output}")
    if result["errors"]:
        for error in result["errors"]:
            print(f"ERROR: {error}")


if __name__ == "__main__":
    main()
