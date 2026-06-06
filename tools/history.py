from typing import Literal

import client

_RANGE = {"short": "short_term", "medium": "medium_term", "long": "long_term"}
_API_MAX = 50  # Spotify top items APIの上限（ページネーションしても50件まで）


def get_recently_played(limit: int = 50) -> dict:
    """最近再生した曲を返す。limit は 1-50（API上限）"""
    limit = min(limit, _API_MAX)
    return client.api_get(f"/me/player/recently-played?limit={limit}")


def get_top_tracks(
    time_range: Literal["short", "medium", "long"] = "short",
    limit: int = 50,
) -> dict:
    """よく聴く曲を返す。time_range: short=4週間 / medium=6ヶ月 / long=数年。limit は最大50（API上限）"""
    limit = min(limit, _API_MAX)
    return client.api_get(f"/me/top/tracks?time_range={_RANGE[time_range]}&limit={limit}")


def get_genre_profile(
    time_range: Literal["short", "medium", "long"] = "long",
) -> dict:
    """上位アーティスト50人のジャンルタグを集計し、頻度順で返す。time_range: short=4週間 / medium=6ヶ月 / long=数年"""
    result = client.api_get(f"/me/top/artists?time_range={_RANGE[time_range]}&limit={_API_MAX}")

    if "error" in result:
        return result

    genre_count: dict[str, int] = {}
    artist_genres: list[dict] = []

    for artist in result.get("items", []):
        genres = artist.get("genres", [])
        name = artist.get("name", "")
        popularity = artist.get("popularity", 0)
        artist_genres.append({"artist": name, "popularity": popularity, "genres": genres})
        for g in genres:
            genre_count[g] = genre_count.get(g, 0) + 1

    sorted_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)

    return {
        "genre_ranking": [{"genre": g, "count": c} for g, c in sorted_genres],
        "artist_count": len(result.get("items", [])),
        "artist_details": artist_genres,
    }


def get_top_artists(
    time_range: Literal["short", "medium", "long"] = "short",
    limit: int = 50,
) -> dict:
    """よく聴くアーティストを返す。time_range: short=4週間 / medium=6ヶ月 / long=数年。limit は最大50（API上限）"""
    limit = min(limit, _API_MAX)
    return client.api_get(f"/me/top/artists?time_range={_RANGE[time_range]}&limit={limit}")
