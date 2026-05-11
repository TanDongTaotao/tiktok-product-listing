from __future__ import annotations

import argparse
import hashlib
import hmac
import http.client
import io
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

TIKTOK_UPLOAD_PATH = "/product/202309/images/upload"
BASE_URL = "https://open-api.tiktokglobalshop.com"
SECRET_KEYS = {"app_secret", "access_token", "refresh_token"}


def load_env(path: str | Path = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return os.environ
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key, value)
    return os.environ


def make_sign(path: str, params: dict[str, Any], app_secret: str, body: str = "") -> str:
    pieces = [path]
    for key in sorted(k for k in params if k not in {"sign", "access_token"}):
        pieces.append(f"{key}{params[key]}")
    if body:
        pieces.append(body)
    base = app_secret + "".join(pieces) + app_secret
    return hmac.new(app_secret.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()


def is_url(source: str) -> bool:
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def download_image(url: str, timeout: int = 30) -> bytes:
    req = Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    with urlopen(req, timeout=timeout) as response:
        data = response.read()
    if not data:
        raise RuntimeError(f"Empty response downloading {url}")
    return data


def process_image(source: str, app_key: str, app_secret: str, access_token: str) -> dict[str, Any]:
    if is_url(source):
        data = download_image(source)
        file_name = Path(urlparse(source).path).name
    else:
        data = Path(source).read_bytes()
        file_name = Path(source).name

    # Build multipart/form-data body with "data" as field name
    boundary = "----FormBoundary" + str(int(time.time() * 1000))
    crlf = b"\r\n"
    body_buf = io.BytesIO()
    body_buf.write(b"--" + boundary.encode() + crlf)
    body_buf.write(b'Content-Disposition: form-data; name="data"; filename="' + file_name.encode() + b'"' + crlf)
    body_buf.write(b"Content-Type: image/jpeg" + crlf)
    body_buf.write(crlf)
    body_buf.write(data)
    body_buf.write(crlf)
    body_buf.write(b"--" + boundary.encode() + b"--" + crlf)
    body_bytes = body_buf.getvalue()

    # Sign with empty body for multipart
    params = {
        "app_key": app_key,
        "timestamp": str(int(time.time())),
    }
    params["sign"] = make_sign(TIKTOK_UPLOAD_PATH, params, app_secret, "")
    url = BASE_URL + TIKTOK_UPLOAD_PATH + "?" + urlencode(params)
    parsed = urlparse(url)

    conn = http.client.HTTPSConnection(parsed.hostname, timeout=60)
    conn.request(
        "POST",
        parsed.path + "?" + parsed.query,
        body=body_bytes,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "x-tts-access-token": access_token,
        },
    )
    resp = conn.getresponse()
    response_data = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return response_data


def parse_args():
    parser = argparse.ArgumentParser(description="Upload product images to TikTok Shop.")
    parser.add_argument("sources", nargs="+", help="Image URLs or file paths")
    parser.add_argument("--shop-cipher", required=True, help="Shop cipher (required for product creation, not for upload)")
    parser.add_argument("--output", default="data/tiktok_product_listing/image_uploads.json")
    parser.add_argument("--env", default=".env")
    return parser.parse_args()


def redact_secrets(value):
    if isinstance(value, dict):
        return {k: redact_secrets(v) for k, v in value.items()}
    return value


def main():
    args = parse_args()
    load_env(args.env)
    app_key = os.environ.get("TIKTOK_SHOP_APP_KEY", "")
    app_secret = os.environ.get("TIKTOK_SHOP_APP_SECRET", "")
    access_token = os.environ.get("TIKTOK_SHOP_ACCESS_TOKEN", "")

    results = []
    for source in args.sources:
        try:
            result = process_image(source, app_key, app_secret, access_token)
            results.append({"source": source, "status": "done", "response": result})
        except Exception as exc:
            results.append({"source": source, "status": "error", "error": f"{type(exc).__name__}: {exc}"})

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(redact_secrets(results), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    done = sum(1 for r in results if r["status"] == "done")
    failed = sum(1 for r in results if r["status"] == "error")
    print(f"Uploaded {done} images, {failed} failed")
    if failed:
        for r in results:
            if r["status"] == "error":
                print(f"  FAIL: {r['source']} - {r['error']}")


if __name__ == "__main__":
    main()
