import client

_user_id: str | None = None


def _get_user_id() -> str:
    global _user_id
    if not _user_id:
        result = client.api_get("/me")
        user_id = result.get("id", "")
        if not user_id:
            raise RuntimeError(f"Failed to get user ID: {result}")
        _user_id = user_id
    return _user_id


def get_playlists() -> dict:
    """自分のプレイリスト一覧を返す"""
    return client.api_get("/me/playlists?limit=50")


def get_playlist_tracks(playlist_id: str) -> dict:
    """プレイリストの曲一覧を返す。各曲に name / artist / uri が含まれる"""
    result = client.api_get(f"/playlists/{playlist_id}")
    if "error" in result:
        return result
    tracks = []
    for entry in result.get("items", {}).get("items", []):
        t = entry.get("item") or entry.get("track") or {}
        if t.get("name"):
            tracks.append({
                "name": t["name"],
                "artist": t["artists"][0]["name"] if t.get("artists") else "",
                "uri": t.get("uri", ""),
            })
    return {"tracks": tracks}


def create_playlist(name: str, description: str = "") -> dict:
    """非公開プレイリストを作成する"""
    return client.api_post(
        "/me/playlists",
        {"name": name, "description": description, "public": False},
    )


def add_tracks_to_playlist(playlist_id: str, uris: list[str]) -> dict:
    """プレイリストに曲を追加する。uri は search_tracks で取得できる"""
    return client.api_post(f"/playlists/{playlist_id}/items", {"uris": uris})


def remove_tracks_from_playlist(playlist_id: str, uris: list[str]) -> dict:
    """プレイリストから曲を削除する"""
    return client.api_delete(
        f"/playlists/{playlist_id}/items",
        {"tracks": [{"uri": u} for u in uris]},
    )
