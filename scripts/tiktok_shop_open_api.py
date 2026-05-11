from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

SECRET_KEYS = {"app_secret", "access_token", "refresh_token"}


@dataclass(frozen=True)
class OpenApiConfig:
    app_key: str
    app_secret: str
    access_token: str
    base_url: str = "https://open-api.tiktokglobalshop.com"


def load_env_file(path: str | Path = ".env", env: dict[str, str] | None = None) -> dict[str, str]:
    target = os.environ if env is None else env
    env_path = Path(path)
    if not env_path.exists():
        return target

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        target.setdefault(key, value)
    return target


def config_from_env(env_path: str | Path = ".env") -> OpenApiConfig:
    load_env_file(env_path)
    missing = [
        key
        for key in ("TIKTOK_SHOP_APP_KEY", "TIKTOK_SHOP_APP_SECRET", "TIKTOK_SHOP_ACCESS_TOKEN")
        if not os.environ.get(key)
    ]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))

    return OpenApiConfig(
        app_key=os.environ["TIKTOK_SHOP_APP_KEY"],
        app_secret=os.environ["TIKTOK_SHOP_APP_SECRET"],
        access_token=os.environ["TIKTOK_SHOP_ACCESS_TOKEN"],
    )


def make_sign(path: str, params: dict[str, Any], app_secret: str, body: str = "") -> str:
    pieces = [path]
    for key in sorted(k for k in params if k not in {"sign", "access_token"}):
        pieces.append(f"{key}{params[key]}")
    if body:
        pieces.append(body)
    base = app_secret + "".join(pieces) + app_secret
    return hmac.new(app_secret.encode("utf-8"), base.encode("utf-8"), hashlib.sha256).hexdigest()


def build_signed_url(
    config: OpenApiConfig,
    path: str,
    params: dict[str, Any] | None = None,
    body: str = "",
    timestamp: str | None = None,
) -> str:
    import time

    query = dict(params or {})
    query["app_key"] = config.app_key
    query["timestamp"] = timestamp or str(int(time.time()))
    query["sign"] = make_sign(path, query, config.app_secret, body)
    return config.base_url + path + "?" + urllib.parse.urlencode(query)


def force_ipv4():
    original_getaddrinfo = socket.getaddrinfo

    def ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = ipv4_only_getaddrinfo


def request_json(
    config: OpenApiConfig,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    body_text = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body is not None else ""
    url = build_signed_url(config, path, params, body_text)
    data = body_text.encode("utf-8") if body_text else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("content-type", "application/json")
    request.add_header("x-tts-access-token", config.access_token)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"local_error": "HTTPError", "status": exc.code, "body": raw}


def redact_secrets(value):
    if isinstance(value, dict):
        redacted = {}
        for key, child in value.items():
            if key.lower() in SECRET_KEYS and isinstance(child, str):
                redacted[key] = child[:8] + "...REDACTED" if child else child
            else:
                redacted[key] = redact_secrets(child)
        return redacted
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value
