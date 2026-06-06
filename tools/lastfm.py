import os
import urllib.parse

import httpx

_BASE = "https://ws.audioscrobbler.com/2.0/"
_TIMEOUT = 10.0


def _api_key() -> str:
    key = os.environ.get("LASTFM_API_KEY", "")
    if not key:
        raise RuntimeError("LASTFM_API_KEY が設定されていません")
    return key


def _get(params: dict) -> dict:
    params = {**params, "api_key": _api_key(), "format": "json"}
    response = httpx.get(_BASE, params=params, timeout=_TIMEOUT)
    if response.is_error:
        return {"error": response.status_code, "message": response.text}
    data = response.json()
    if "error" in data:
        return {"error": data["error"], "message": data.get("message", "")}
    return data


def get_similar_artists(artist_name: str, limit: int = 10) -> dict:
    """Last.fm から類似アーティストを取得する。match スコア（0〜1）付きで返す"""
    data = _get({"method": "artist.getsimilar", "artist": artist_name, "limit": limit, "autocorrect": 1})
    similar = data.get("similarartists", {}).get("artist", [])
    return {
        "similar_artists": [
            {"name": a["name"], "match": float(a["match"]), "url": a["url"]}
            for a in similar
        ]
    }


def get_artist_top_tags(artist_name: str) -> dict:
    """Last.fm コミュニティによるアーティストのジャンルタグを取得する（Spotifyより細かい）"""
    data = _get({"method": "artist.gettoptags", "artist": artist_name, "autocorrect": 1})
    tags = data.get("toptags", {}).get("tag", [])
    return {
        "artist": artist_name,
        "tags": [{"name": t["name"], "count": int(t["count"])} for t in tags[:20]],
    }


def get_artist_info(artist_name: str) -> dict:
    """アーティストの概要・月間リスナー数・再生数・上位タグ・バイオ（要約）を返す"""
    data = _get({"method": "artist.getinfo", "artist": artist_name, "autocorrect": 1, "lang": "ja"})
    artist = data.get("artist", {})
    stats = artist.get("stats", {})
    tags = artist.get("tags", {}).get("tag", [])
    bio = artist.get("bio", {})
    return {
        "name": artist.get("name", ""),
        "listeners": int(stats.get("listeners", 0)),
        "playcount": int(stats.get("playcount", 0)),
        "tags": [t["name"] for t in tags],
        "bio_summary": bio.get("summary", "").split("<a href")[0].strip(),
        "url": artist.get("url", ""),
    }


def get_album_info(artist_name: str, album_name: str) -> dict:
    """アルバムのタグ・リスナー数・再生数・収録曲を返す"""
    data = _get({"method": "album.getinfo", "artist": artist_name, "album": album_name, "autocorrect": 1})
    album = data.get("album", {})
    tags = album.get("tags", {}).get("tag", [])
    tracks = album.get("tracks", {}).get("track", [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    return {
        "name": album.get("name", ""),
        "artist": album.get("artist", ""),
        "listeners": int(album.get("listeners", 0)),
        "playcount": int(album.get("playcount", 0)),
        "tags": [t["name"] for t in tags],
        "tracks": [t["name"] for t in tracks],
        "url": album.get("url", ""),
    }


def get_similar_tracks(artist_name: str, track_name: str, limit: int = 10) -> dict:
    """Last.fm から類似曲を取得する。キュー追加や曲探しに使う"""
    data = _get({"method": "track.getsimilar", "artist": artist_name, "track": track_name, "limit": limit, "autocorrect": 1})
    tracks = data.get("similartracks", {}).get("track", [])
    return {
        "similar_tracks": [
            {
                "name": t["name"],
                "artist": t["artist"]["name"],
                "match": float(t["match"]),
                "url": t["url"],
            }
            for t in tracks
        ]
    }


def get_tag_top_artists(tag: str, limit: int = 50) -> dict:
    """Last.fm タグに紐づく上位アーティストを返す（genre_bridge で使用）"""
    data = _get({"method": "tag.gettopartists", "tag": tag, "limit": limit})
    artists = data.get("topartists", {}).get("artist", [])
    return {
        "tag": tag,
        "artists": [{"name": a["name"], "url": a.get("url", "")} for a in artists],
    }
