import argparse
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CALLBACK_PATH = "/auth/tiktok/callback"


def build_payload(raw_path):
    parsed = urlparse(raw_path)
    query = parse_qs(parsed.query)
    code = query.get("code", [""])[0]
    if not code:
        return None

    return {
        "code": code,
        "state": query.get("state", [""])[0],
        "shop_region": query.get("shop_region", [""])[0],
        "locale": query.get("locale", [""])[0],
        "path": parsed.path,
        "raw_url": raw_path,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def write_payload(output_path, payload):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_handler(output_path):
    output_path = Path(output_path)

    class TikTokOAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != CALLBACK_PATH:
                self.send_text(404, "Not found\n")
                return

            payload = build_payload(self.path)
            if payload is None:
                self.send_text(400, "Missing required query parameter: code\n")
                return

            write_payload(output_path, payload)
            print(f"Captured TikTok OAuth code for shop_region={payload['shop_region'] or 'unknown'}")
            print(f"Saved callback payload to {output_path}")
            self.send_html(
                200,
                "<html><body><h1>Authorization code received</h1>"
                "<p>You can close this page.</p></body></html>",
            )

        def log_message(self, format, *args):
            print(f"{self.address_string()} - {format % args}")

        def send_text(self, status, body):
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "text/plain; charset=utf-8")
            self.send_header("content-length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def send_html(self, status, body):
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return TikTokOAuthCallbackHandler


def parse_args():
    parser = argparse.ArgumentParser(description="Capture TikTok Shop OAuth callback codes locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--output", default="data/tiktok_oauth_callback.json")
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output)
    handler = create_handler(output_path)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    callback_url = f"http://{args.host}:{args.port}{CALLBACK_PATH}"
    print(f"Listening on {callback_url}")
    print(f"Writing callback payloads to {output_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down callback server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
