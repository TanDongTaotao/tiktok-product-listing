"""TikTok category attribute value ID mapping.
Generated from TikTok API responses. Maps Chinese column names and English value names to TikTok attribute/value IDs.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

_CACHE: dict[str, Any] | None = None

# Path to cached API data with full value lists
_CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "tiktok_product_listing" / "all_category_attributes_full.json"


def _load_cache() -> dict[str, Any]:
    global _CACHE
    if _CACHE is None:
        if _CACHE_PATH.exists():
            _CACHE = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        else:
            _CACHE = {}
    return _CACHE


def _build_attr_name_to_id() -> dict[str, dict[str, str]]:
    """Build mapping: category_id → { english_name_lower → attribute_id }"""
    cache = _load_cache()
    result = {}
    for cat_id, cat_data in cache.items():
        mapping = {}
        for attr in cat_data.get("attributes", []):
            mapping[attr["name"].lower()] = attr["id"]
        result[cat_id] = mapping
    return result


def _build_value_name_to_id() -> dict[str, dict[str, str]]:
    """Build mapping: attribute_id → { value_name_lower → value_id }"""
    cache = _load_cache()
    result = {}
    for cat_data in cache.values():
        for attr in cat_data.get("attributes", []):
            aid = attr["id"]
            if aid not in result:
                result[aid] = {}
            for val in attr.get("values", []):
                result[aid][val["name"].lower()] = val["id"]
    return result


def get_attribute_id(category_id: str, attr_name: str) -> str | None:
    """Get TikTok attribute ID for a category and attribute name."""
    mapping = _build_attr_name_to_id()
    cat_map = mapping.get(category_id, {})
    return cat_map.get(attr_name.lower())


def get_value_id(attribute_id: str, value_name: str) -> str | None:
    """Get TikTok value ID for an attribute and value name."""
    mapping = _build_value_name_to_id()
    attr_map = mapping.get(attribute_id, {})
    return attr_map.get(value_name.lower())


def get_all_value_ids(attribute_id: str) -> dict[str, str]:
    """Get all value IDs for an attribute."""
    mapping = _build_value_name_to_id()
    return mapping.get(attribute_id, {})


def category_columns_to_attributes(category_id: str, columns: dict[str, str]) -> list[dict[str, Any]]:
    """Convert Excel column name→value dict to TikTok product_attributes.

    Args:
        category_id: TikTok leaf category ID (e.g. "601281")
        columns: dict mapping Chinese column name to value (e.g. {"材质": "Cotton"})

    Returns:
        List of {"id": attr_id, "values": [{"id": value_id, "name": value_name}]}
    """
    attr_name_map = _build_attr_name_to_id()
    value_id_map = _build_value_name_to_id()

    # Chinese column name → English attribute name mapping
    chinese_to_english = {
        "材质": "Materials",
        "季节": "Season",
        "风格": "Style",
        "裙长": "Dress Length",
        "原产国": "Country of origin",
        "袖长": "Sleeve Length",
        "领型": "Neckline",
        "闭合方式": "Closure Type",
        "袖型": "Sleeve Type",
        "图案": "Pattern",
        "版型": "Clothing Type",
        "装饰": "Embellishment",
        "腰高": "Waist Height",
        "裤长": "Hem Length",
        "裤型": "Inseam Style",
        "领型款式": "Collar Type",
        "钢圈类型": "Bra Coverage",
        "肩带类型": "Strap Type",
        "罩杯类型": "Bra Type",
        "内裤款式": "Panties Style",
        "泳衣类型": "Swimwear Type",
        "运动特性": "Sports Feature",
        "运动类型": "Sports Type",
        "袜高": "Item Length Description",
        "类型": "Socks Type",
    }

    cat_attr_map = attr_name_map.get(category_id, {})
    result = []

    for cn_name, value in columns.items():
        if not value or not value.strip():
            continue
        value = value.strip()
        eng_name = chinese_to_english.get(cn_name)
        if not eng_name:
            continue

        attr_id = cat_attr_map.get(eng_name.lower())
        if not attr_id:
            continue

        val_id = value_id_map.get(attr_id, {}).get(value.lower())
        if not val_id:
            continue

        result.append({
            "id": attr_id,
            "values": [{"id": val_id, "name": value}],
        })

    return result
