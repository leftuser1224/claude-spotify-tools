import urllib.parse

import client


def search_tracks(query: str, limit: int = 5) -> dict:
    """曲を検索する。結果に uri が含まれるので play_track に渡せる"""
    return client.api_get(f"/search?q={urllib.parse.quote_plus(query)}&type=track&limit={limit}&market=JP")


def search_artists(query: str, limit: int = 5) -> dict:
    """アーティストを検索する"""
    return client.api_get(f"/search?q={urllib.parse.quote_plus(query)}&type=artist&limit={limit}&market=JP")


def search_albums(query: str, limit: int = 5) -> dict:
    """アルバムを検索する。結果に uri が含まれるので play_context に渡せる"""
    return client.api_get(f"/search?q={urllib.parse.quote_plus(query)}&type=album&limit={limit}&market=JP")


def search_playlists(query: str, limit: int = 5) -> dict:
    """パブリックプレイリストを検索する。結果に uri が含まれるので play_context に渡せる"""
    return client.api_get(f"/search?q={urllib.parse.quote_plus(query)}&type=playlist&limit={limit}&market=JP")


def get_this_is_playlist(artist_name: str) -> dict:
    """
    アーティストの公式 Spotify「This Is」プレイリストを取得する。
    まずアーティストの正式名称を取得し、その名前で検索して owner が spotify の
    プレイリストを優先的に返す。見つからなければ最も一致するものを返す。
    """
    # Step 1: アーティストの正式名称を取得
    artist_result = client.api_get(
        f"/search?q={urllib.parse.quote_plus(artist_name)}&type=artist&limit=1&market=JP"
    )
    spotify_artist_name = artist_name
    try:
        items = artist_result["artists"]["items"]
        if items:
            spotify_artist_name = items[0]["name"]
    except (KeyError, IndexError, TypeError):
        pass

    # Step 2: 「This Is {artist_name}」で検索（market=JP で null を排除）
    query = f'"This Is" {spotify_artist_name}'
    result = client.api_get(
        f"/search?q={urllib.parse.quote_plus(query)}&type=playlist&limit=10&market=JP"
    )

    try:
        playlists = [p for p in result["playlists"]["items"] if p is not None]
    except (KeyError, TypeError):
        return {"error": "検索結果を取得できませんでした"}

    if not playlists:
        return {"found": False, "artist_name": spotify_artist_name, "playlists": []}

    # Step 3: Spotify 公式を最優先、次に名前一致度でソート
    target_name = f"This Is {spotify_artist_name}".lower()

    def score(p: dict) -> tuple:
        is_official = p.get("owner", {}).get("id") == "spotify"
        name_match = p.get("name", "").lower() == target_name
        track_count = p.get("items", {}).get("total", 0)
        return (is_official, name_match, track_count)

    playlists.sort(key=score, reverse=True)
    best = playlists[0]

    return {
        "found": True,
        "artist_name": spotify_artist_name,
        "playlist": {
            "name": best.get("name"),
            "owner": best.get("owner", {}).get("display_name"),
            "owner_id": best.get("owner", {}).get("id"),
            "is_official": best.get("owner", {}).get("id") == "spotify",
            "total_tracks": best.get("items", {}).get("total"),
            "uri": best.get("uri"),
            "url": best.get("external_urls", {}).get("spotify"),
        },
    }
