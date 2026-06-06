import json

import httpx

import auth

BASE_URL = "https://api.spotify.com/v1"
_TIMEOUT = 10.0


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.get_access_token()}"}


def _parse(response: httpx.Response) -> dict:
    if not response.content:
        return {}
    try:
        return response.json()
    except (ValueError, json.JSONDecodeError):
        return {}


def _error(response: httpx.Response) -> dict:
    try:
        return {"error": response.status_code, "message": response.json()}
    except (ValueError, json.JSONDecodeError):
        return {"error": response.status_code, "message": response.text}


def _request(method: str, path: str, **kwargs: object) -> dict:
    response = httpx.request(method, f"{BASE_URL}{path}", headers=_headers(), timeout=_TIMEOUT, **kwargs)
    if response.status_code == 401:
        auth.invalidate()
        response = httpx.request(method, f"{BASE_URL}{path}", headers=_headers(), timeout=_TIMEOUT, **kwargs)
    if response.is_error:
        return _error(response)
    return _parse(response)


def api_get(path: str) -> dict:
    return _request("GET", path)


def api_post(path: str, data: dict | None = None) -> dict:
    return _request("POST", path, json=data)


def api_put(path: str, data: dict | None = None) -> dict:
    return _request("PUT", path, json=data)


def api_delete(path: str, data: dict | None = None) -> dict:
    return _request("DELETE", path, json=data)
