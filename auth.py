import base64
import http.server
import json
import os
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID: str = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET: str = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
REDIRECT_URI: str = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
REFRESH_TOKEN_ENV: str = os.environ.get("SPOTIFY_REFRESH_TOKEN", "")
SCOPES = " ".join([
    "user-read-recently-played", "user-top-read",
    "user-read-currently-playing", "user-read-playback-state",
    "user-modify-playback-state", "user-library-read", "user-library-modify",
    "playlist-read-private", "playlist-read-collaborative",
    "playlist-modify-public", "playlist-modify-private", "user-read-private",
    "user-follow-read", "user-follow-modify",
])
TOKEN_FILE = Path(__file__).parent / ".cache" / "token.json"

_access_token: str | None = None


def _auth_header() -> str:
    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    return f"Basic {credentials}"


def _load_saved() -> dict | None:
    try:
        return json.loads(TOKEN_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save(data: dict) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(data))


def _refresh(saved: dict) -> str:
    response = httpx.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": _auth_header()},
        data={"grant_type": "refresh_token", "refresh_token": saved["refresh_token"]},
    )
    response.raise_for_status()
    data = response.json()
    if "access_token" not in data:
        raise ValueError(f"Missing access_token in response: {data}")
    updated = {**saved, "access_token": data["access_token"]}
    if "refresh_token" in data:
        updated["refresh_token"] = data["refresh_token"]
    if "scope" in data:
        updated["scope"] = data["scope"]
    _save(updated)
    return data["access_token"]


def _browser_auth() -> str:
    params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    })
    url = f"https://accounts.spotify.com/authorize?{params}"
    if not webbrowser.open(url):
        print(f"ブラウザを開けませんでした。以下のURLにアクセスしてください:\n{url}", file=sys.stderr)

    code: list[str] = []

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in parsed:
                code.append(parsed["code"][0])
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("認証完了。このタブを閉じてください。".encode())
            else:
                self.send_response(400)
                self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    server = http.server.HTTPServer(("127.0.0.1", 8888), _Handler)
    server.timeout = 120
    server.handle_request()

    if not code:
        raise RuntimeError("OAuth callback did not return a code")

    response = httpx.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": _auth_header()},
        data={
            "grant_type": "authorization_code",
            "code": code[0],
            "redirect_uri": REDIRECT_URI,
        },
    )
    response.raise_for_status()
    result = response.json()
    if "access_token" not in result:
        raise ValueError(f"Missing access_token in response: {result}")
    _save(result)
    return result["access_token"]


def _scopes_ok(saved: dict) -> bool:
    granted = set(saved.get("scope", "").split())
    return set(SCOPES.split()).issubset(granted)


def get_access_token() -> str:
    global _access_token
    if _access_token:
        return _access_token
    saved = _load_saved()
    if not saved and REFRESH_TOKEN_ENV:
        saved = {"refresh_token": REFRESH_TOKEN_ENV, "scope": SCOPES}
    if saved and "refresh_token" in saved and _scopes_ok(saved):
        try:
            _access_token = _refresh(saved)
            return _access_token
        except (httpx.HTTPError, KeyError, ValueError):
            pass
    _access_token = _browser_auth()
    return _access_token


def invalidate() -> None:
    global _access_token
    _access_token = None


def check_env() -> None:
    missing = [k for k in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    check_env()
    TOKEN_FILE.unlink(missing_ok=True)
    token = _browser_auth()
    print("認証完了。MCPサーバーを再起動してください。")
