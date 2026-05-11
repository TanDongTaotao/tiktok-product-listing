from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tiktok_shop_open_api import config_from_env, force_ipv4, redact_secrets, request_json

DEFAULT_SEEDS = ["women dress", "women t-shirt", "leggings", "socks"]
OUTPUT_DIR = Path("data/tiktok_product_listing")


class TikTokShopClient:
    def __init__(self, env_path: str = ".env", ipv4: bool = True):
        if ipv4:
            force_ipv4()
        self.config = config_from_env(env_path)

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return request_json(self.config, "GET", path, params=params)

    def post(self, path: str, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return request_json(self.config, "POST", path, params=params, body=body)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def choose_shop(shops: list[dict[str, Any]], shop_cipher: str | None = None) -> dict[str, Any]:
    if not shops:
        raise RuntimeError("No authorized shops returned by TikTok Shop API")
    if shop_cipher:
        for shop in shops:
            if shop.get("cipher") == shop_cipher:
                return shop
        raise RuntimeError(f"Requested shop_cipher was not found: {shop_cipher}")
    for shop in shops:
        if shop.get("region") == "US":
            return shop
    return shops[0]


def summarize_prerequisites(response: dict[str, Any]) -> dict[str, Any]:
    check_results = ((response.get("data") or {}).get("check_results") or [])
    failed_items = [
        {
            "check_item": item.get("check_item"),
            "fail_reasons": item.get("fail_reasons") or [],
        }
        for item in check_results
        if item.get("is_failed")
    ]
    return {
        "total_count": len(check_results),
        "failed_count": len(failed_items),
        "failed_items": failed_items,
    }


def run_precheck(client, shop_cipher: str | None = None) -> dict[str, Any]:
    shops_response = client.get("/authorization/202309/shops")
    shops = ((shops_response.get("data") or {}).get("shops") or [])
    shop = choose_shop(shops, shop_cipher)
    prerequisites_response = client.get(
        "/product/202312/prerequisites",
        {"shop_cipher": shop["cipher"]},
    )
    return {
        "generated_at": utc_now(),
        "shop": shop,
        "authorized_shops_response": shops_response,
        "listing_prerequisites_response": prerequisites_response,
        "summary": summarize_prerequisites(prerequisites_response),
    }


def leaf_categories(*responses: dict[str, Any], max_count: int) -> list[dict[str, Any]]:
    seen = set()
    leaves = []
    for response in responses:
        categories = ((response.get("data") or {}).get("categories") or [])
        for category in categories:
            category_id = str(category.get("id") or "")
            if not category_id or category_id in seen or not category.get("is_leaf"):
                continue
            seen.add(category_id)
            leaves.append(category)
            if len(leaves) >= max_count:
                return leaves
    return leaves


def recommendation_body(seed: str) -> dict[str, Any]:
    return {
        "product_title": seed.title(),
        "description": f"<p>{seed.title()} for everyday outfits. Comfortable fit and easy styling.</p>",
        "category_version": "v2",
        "listing_platform": "TIKTOK_SHOP",
    }


def discover_categories(
    client,
    shop: dict[str, Any],
    seeds: list[str] | None = None,
    max_leaf_categories: int = 3,
) -> dict[str, Any]:
    selected_seeds = seeds or DEFAULT_SEEDS
    results = []
    for seed in selected_seeds:
        category_response = client.get(
            "/product/202309/categories",
            {
                "shop_cipher": shop["cipher"],
                "category_version": "v2",
                "locale": "en-US",
                "keyword": seed,
                "listing_platform": "TIKTOK_SHOP",
            },
        )
        recommend_response = client.post(
            "/product/202309/categories/recommend",
            {"shop_cipher": shop["cipher"]},
            recommendation_body(seed),
        )
        candidates = leaf_categories(category_response, recommend_response, max_count=max_leaf_categories)
        enriched = []
        for category in candidates:
            category_id = str(category["id"])
            common_params = {
                "shop_cipher": shop["cipher"],
                "category_version": "v2",
            }
            rules_response = client.get(f"/product/202309/categories/{category_id}/rules", common_params)
            attributes_response = client.get(
                f"/product/202309/categories/{category_id}/attributes",
                {**common_params, "locale": "en-US"},
            )
            enriched.append(
                {
                    "category": category,
                    "rules_response": rules_response,
                    "attributes_response": attributes_response,
                    "mandatory_attributes": mandatory_attributes(attributes_response),
                }
            )
        results.append(
            {
                "seed": seed,
                "category_response": category_response,
                "recommend_response": recommend_response,
                "leaf_candidates": candidates,
                "enriched_categories": enriched,
            }
        )
    return {
        "generated_at": utc_now(),
        "shop": shop,
        "seeds": selected_seeds,
        "results": results,
    }


def mandatory_attributes(attributes_response: dict[str, Any]) -> list[dict[str, Any]]:
    attributes = ((attributes_response.get("data") or {}).get("attributes") or [])
    return [attribute for attribute in attributes if attribute.get("is_requried") or attribute.get("is_required")]


def write_json(path: Path, payload: dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_secrets(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_precheck_summary(result: dict[str, Any]):
    shop = result["shop"]
    summary = result["summary"]
    print(f"Shop: {shop.get('name')} ({shop.get('region')}, {shop.get('seller_type')})")
    print(f"Prerequisite checks: {summary['total_count']} total, {summary['failed_count']} failed")
    for item in summary["failed_items"]:
        print(f"- {item['check_item']}: {'; '.join(item['fail_reasons'])}")


def parse_args():
    parser = argparse.ArgumentParser(description="Run TikTok Shop product listing prechecks.")
    parser.add_argument("command", choices=["precheck", "discover-categories", "all"])
    parser.add_argument("--env", default=".env")
    parser.add_argument("--shop-cipher")
    parser.add_argument("--no-ipv4", action="store_true")
    parser.add_argument("--seed", action="append", dest="seeds")
    parser.add_argument("--max-leaf-categories", type=int, default=3)
    return parser.parse_args()


def main():
    args = parse_args()
    client = TikTokShopClient(args.env, ipv4=not args.no_ipv4)
    precheck_result = None
    if args.command in {"precheck", "all"}:
        precheck_result = run_precheck(client, args.shop_cipher)
        write_json(OUTPUT_DIR / "precheck.json", precheck_result)
        print_precheck_summary(precheck_result)

    if args.command in {"discover-categories", "all"}:
        if precheck_result is None:
            precheck_result = run_precheck(client, args.shop_cipher)
        categories_result = discover_categories(
            client,
            precheck_result["shop"],
            seeds=args.seeds,
            max_leaf_categories=args.max_leaf_categories,
        )
        write_json(OUTPUT_DIR / "categories.json", categories_result)
        print(f"Category discovery seeds: {len(categories_result['seeds'])}")
        print(f"Wrote {OUTPUT_DIR / 'categories.json'}")


if __name__ == "__main__":
    main()
