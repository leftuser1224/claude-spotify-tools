"""
Spotify × Last.fm 複合ディスカバリーツール

Spotify の聴取データと Last.fm の音楽グラフを組み合わせて、
どちらか単体では実現できない音楽発掘体験を提供する。
"""
from typing import Literal

import client
from tools import lastfm as _lastfm

_RANGE = {"short": "short_term", "medium": "medium_term", "long": "long_term"}
_API_MAX = 50


# ─── アーティスト系 ──────────────────────────────────────────


def build_taste_profile(time_range: Literal["short", "medium", "long"] = "long") -> dict:
    """
    Spotifyの上位アーティスト × Last.fmコミュニティタグで
    再生頻度で重み付けした音楽DNAプロファイルを生成する。
    単なるジャンルタグ列挙ではなく「全体の何%」まで算出する。
    """
    result = client.api_get(f"/me/top/artists?time_range={_RANGE[time_range]}&limit={_API_MAX}")
    artists = result.get("items", [])

    tag_weights: dict[str, float] = {}
    artist_profiles = []

    for rank, artist in enumerate(artists[:20]):
        name = artist["name"]
        weight = float(_API_MAX - rank)  # 上位ほど重み大

        tags_data = _lastfm.get_artist_top_tags(name)
        tags = tags_data.get("tags", [])[:5]

        for tag in tags:
            tag_name = tag["name"].lower()
            tag_weight = tag["count"] / 100.0
            tag_weights[tag_name] = tag_weights.get(tag_name, 0.0) + weight * tag_weight

        artist_profiles.append({
            "name": name,
            "rank": rank + 1,
            "popularity": artist.get("popularity", 0),
            "spotify_genres": artist.get("genres", []),
            "lastfm_tags": [t["name"] for t in tags],
        })

    total = sum(tag_weights.values()) or 1.0
    ranked_tags = sorted(tag_weights.items(), key=lambda x: -x[1])[:20]
    genre_breakdown = [
        {"tag": tag, "weight_pct": round(w / total * 100, 1)}
        for tag, w in ranked_tags
    ]

    return {
        "time_range": time_range,
        "artists_analyzed": len(artist_profiles),
        "genre_breakdown": genre_breakdown,
        "artist_profiles": artist_profiles,
    }


def find_hidden_gems(
    min_listeners: int = 50000,
    max_listeners: int = 500000,
    limit: int = 10,
    time_range: Literal["short", "medium", "long"] = "long",
) -> dict:
    """
    Spotifyの上位アーティストのLast.fm類似アーティストから、
    聴取履歴になく指定リスナー数範囲内の隠れた名アーティストを発掘する。
    min/max_listeners でメジャー〜インディーの規模感を絞れる。
    """
    top_result = client.api_get(f"/me/top/artists?time_range={_RANGE[time_range]}&limit={_API_MAX}")
    known_names = {a["name"].lower() for a in top_result.get("items", [])}

    recent_result = client.api_get("/me/player/recently-played?limit=50")
    for item in recent_result.get("items", []):
        known_names.add(item["track"]["artists"][0]["name"].lower())

    seed_artists = top_result.get("items", [])[:10]
    candidates: dict[str, dict] = {}

    for seed in seed_artists:
        if len(candidates) >= limit * 3:
            break
        similar_data = _lastfm.get_similar_artists(seed["name"], limit=20)
        for s in similar_data.get("similar_artists", []):
            name = s["name"]
            key = name.lower()
            if key in known_names or key in candidates:
                continue
            info = _lastfm.get_artist_info(name)
            listeners = info.get("listeners", 0)
            if min_listeners <= listeners <= max_listeners:
                candidates[key] = {
                    "name": name,
                    "listeners": listeners,
                    "tags": info.get("tags", [])[:5],
                    "similar_to": seed["name"],
                    "match_score": round(s["match"], 3),
                    "lastfm_url": info.get("url", ""),
                }

    gems = sorted(candidates.values(), key=lambda x: -x["match_score"])[:limit]
    return {
        "listener_range": {"min": min_listeners, "max": max_listeners},
        "hidden_gems": gems,
    }


def traverse_artist_graph(
    artist_name: str,
    hops: int = 2,
    branch: int = 5,
) -> dict:
    """
    アーティストから類似→類似と多段探索し
    「好みから2〜3ステップ離れた未知の領域」を発掘する。
    hops=2 で類似の類似、hops=3 でさらに遠い領域まで到達する。
    """
    visited: set[str] = set()
    frontier = [(artist_name, 0, 1.0, [artist_name])]
    discoveries = []

    while frontier:
        name, depth, score, path = frontier.pop(0)
        key = name.lower()
        if key in visited:
            continue
        visited.add(key)

        if depth > 0:
            discoveries.append({
                "name": name,
                "depth": depth,
                "cumulative_score": round(score, 3),
                "discovery_path": " → ".join(path),
            })

        if depth < hops:
            similar = _lastfm.get_similar_artists(name, limit=branch)
            for s in similar.get("similar_artists", []):
                if s["name"].lower() not in visited:
                    frontier.append((
                        s["name"],
                        depth + 1,
                        score * s["match"],
                        path + [s["name"]],
                    ))

    discoveries.sort(key=lambda x: (x["depth"], -x["cumulative_score"]))
    return {
        "seed_artist": artist_name,
        "hops": hops,
        "total_discovered": len(discoveries),
        "discoveries": discoveries[:30],
    }


def genre_bridge(genre_a: str, genre_b: str, limit: int = 10) -> dict:
    """
    2つのジャンルタグ両方に属するアーティストを見つける。
    例：'britpop' と 'shoegaze' 両方のタグを持つアーティストを探す。
    ジャンルの交差点にいる独特なアーティスト発掘に使う。
    """
    data_a = _lastfm.get_tag_top_artists(genre_a, limit=50)
    data_b = _lastfm.get_tag_top_artists(genre_b, limit=50)

    names_b = {a["name"].lower() for a in data_b.get("artists", [])}
    bridges = []

    for artist in data_a.get("artists", []):
        if artist["name"].lower() in names_b:
            bridges.append({"name": artist["name"], "url": artist.get("url", "")})
        if len(bridges) >= limit:
            break

    # リストの交差が少ない場合、タグを直接確認して補完する
    if len(bridges) < 3:
        checked = {b["name"].lower() for b in bridges}
        for artist in data_a.get("artists", [])[:20]:
            if artist["name"].lower() in checked:
                continue
            tags_data = _lastfm.get_artist_top_tags(artist["name"])
            tag_names = [t["name"].lower() for t in tags_data.get("tags", [])]
            if any(genre_b.lower() in tag or tag in genre_b.lower() for tag in tag_names):
                bridges.append({"name": artist["name"], "url": artist.get("url", "")})
            if len(bridges) >= limit:
                break

    return {
        "genre_a": genre_a,
        "genre_b": genre_b,
        "bridge_count": len(bridges),
        "bridge_artists": bridges,
    }


# ─── トラック系 ──────────────────────────────────────────────


def find_similar_tracks_fresh(
    artist_name: str,
    track_name: str,
    limit: int = 10,
) -> dict:
    """
    Last.fmの類似曲からSpotifyの聴取履歴にない曲だけを抽出して返す。
    「この曲が好きだから似た未聴の曲を教えて」というときに使う。
    """
    recent = client.api_get("/me/player/recently-played?limit=50")
    known: set[tuple[str, str]] = set()
    for item in recent.get("items", []):
        t = item["track"]
        known.add((t["name"].lower(), t["artists"][0]["name"].lower()))

    top = client.api_get("/me/top/tracks?time_range=long_term&limit=50")
    for t in top.get("items", []):
        known.add((t["name"].lower(), t["artists"][0]["name"].lower()))

    similar = _lastfm.get_similar_tracks(artist_name, track_name, limit=limit * 3)
    fresh = []
    for t in similar.get("similar_tracks", []):
        key = (t["name"].lower(), t["artist"].lower())
        if key not in known:
            fresh.append(t)
        if len(fresh) >= limit:
            break

    return {
        "seed": f"{artist_name} — {track_name}",
        "fresh_similar_tracks": fresh,
        "known_excluded": len(similar.get("similar_tracks", [])) - len(fresh),
    }


def build_track_taste_profile(
    time_range: Literal["short", "medium", "long"] = "long",
) -> dict:
    """
    上位曲 × Last.fmタグで「ムード・エネルギー・テクスチャ」プロファイルを生成する。
    アーティスト単位ではなく曲単位で集計するため、アルバムや時期ごとの
    細かな聴き方の傾向（例：激しい曲だけよく聴くなど）が浮かび上がる。
    """
    result = client.api_get(f"/me/top/tracks?time_range={_RANGE[time_range]}&limit={_API_MAX}")
    tracks = result.get("items", [])

    tag_weights: dict[str, float] = {}
    track_profiles = []

    for rank, track in enumerate(tracks[:30]):
        artist = track["artists"][0]["name"]
        name = track["name"]
        weight = float(_API_MAX - rank)

        tags_data = _lastfm.get_artist_top_tags(artist)
        tags = tags_data.get("tags", [])[:5]

        for tag in tags:
            tag_name = tag["name"].lower()
            tag_weight = tag["count"] / 100.0
            tag_weights[tag_name] = tag_weights.get(tag_name, 0.0) + weight * tag_weight

        track_profiles.append({
            "rank": rank + 1,
            "track": name,
            "artist": artist,
            "album": track["album"]["name"],
            "lastfm_tags": [t["name"] for t in tags],
        })

    total = sum(tag_weights.values()) or 1.0
    ranked = sorted(tag_weights.items(), key=lambda x: -x[1])[:15]
    mood_profile = [{"tag": t, "weight_pct": round(w / total * 100, 1)} for t, w in ranked]

    return {
        "time_range": time_range,
        "tracks_analyzed": len(track_profiles),
        "mood_profile": mood_profile,
        "track_profiles": track_profiles,
    }


def analyze_listening_evolution() -> dict:
    """
    短期・中期・長期の3期間でジャンル傾向を比較し、音楽趣味の変遷を分析する。
    「最近パンクが増えた」「以前はJロック多かった」という時間軸の変化を可視化する。
    """
    ranges = {"short": "short_term", "medium": "medium_term", "long": "long_term"}

    period_artists: dict[str, list] = {}
    all_artist_tags: dict[str, list] = {}

    for label, term in ranges.items():
        result = client.api_get(f"/me/top/artists?time_range={term}&limit=50")
        artists = result.get("items", [])
        period_artists[label] = artists
        for artist in artists:
            name = artist["name"]
            if name not in all_artist_tags:
                tags_data = _lastfm.get_artist_top_tags(name)
                all_artist_tags[name] = tags_data.get("tags", [])[:5]

    def calc_breakdown(artists: list) -> list:
        tag_weights: dict[str, float] = {}
        for rank, artist in enumerate(artists):
            weight = float(50 - rank)
            for tag in all_artist_tags.get(artist["name"], []):
                tag_name = tag["name"].lower()
                tag_weights[tag_name] = tag_weights.get(tag_name, 0.0) + weight * (tag["count"] / 100.0)
        total = sum(tag_weights.values()) or 1.0
        return [
            {"tag": t, "weight_pct": round(w / total * 100, 1)}
            for t, w in sorted(tag_weights.items(), key=lambda x: -x[1])[:10]
        ]

    short_names = {a["name"] for a in period_artists["short"]}
    medium_names = {a["name"] for a in period_artists["medium"]}
    long_names = {a["name"] for a in period_artists["long"]}

    return {
        "genre_by_period": {
            "short_term":  calc_breakdown(period_artists["short"]),
            "medium_term": calc_breakdown(period_artists["medium"]),
            "long_term":   calc_breakdown(period_artists["long"]),
        },
        "artist_movements": {
            "rising":     sorted(short_names - long_names),      # 最近増えた
            "fading":     sorted(long_names - short_names),      # 以前多かったが最近減った
            "consistent": sorted(short_names & medium_names & long_names),  # 常連
        },
    }


def analyze_discovery_rate() -> dict:
    """
    短期と長期のトップアーティストの重複率から「どれだけ新しい音楽を開拓しているか」を数値化する。
    冒険的リスナー vs 快適ゾーン依存リスナーの傾向を診断する。
    """
    short_result = client.api_get("/me/top/artists?time_range=short_term&limit=50")
    long_result  = client.api_get("/me/top/artists?time_range=long_term&limit=50")

    short_names = {a["name"] for a in short_result.get("items", [])}
    long_names  = {a["name"] for a in long_result.get("items", [])}

    overlap = short_names & long_names
    overlap_rate   = len(overlap) / len(short_names) * 100 if short_names else 0
    discovery_rate = 100.0 - overlap_rate

    if discovery_rate >= 70:
        listener_type = "冒険家（Adventurer）"
        description   = "常に新しい音楽を開拓している"
    elif discovery_rate >= 40:
        listener_type = "バランス型（Explorer）"
        description   = "新旧バランスよく聴いている"
    else:
        listener_type = "快適ゾーン型（Comfortable）"
        description   = "信頼できるアーティストを繰り返し聴く傾向"

    return {
        "discovery_score": round(discovery_rate, 1),
        "overlap_rate":    round(overlap_rate, 1),
        "listener_type":   listener_type,
        "description":     description,
        "new_artists_recently":  sorted(short_names - long_names),
        "consistent_favorites":  sorted(overlap),
    }


def analyze_mood_by_time(utc_offset_hours: int = 9) -> dict:
    """
    最近再生した曲のタイムスタンプ × Last.fmタグで
    「朝・昼・夜・深夜」それぞれどんなムードで聴いているかを分析する。
    utc_offset_hours はタイムゾーン補正用（日本は +9）。
    """
    recent = client.api_get("/me/player/recently-played?limit=50")
    items  = recent.get("items", [])

    time_slots: dict[str, list[str]] = {"morning": [], "afternoon": [], "evening": [], "night": []}

    for item in items:
        played_at = item.get("played_at", "")
        try:
            utc_hour   = int(played_at[11:13])
            local_hour = (utc_hour + utc_offset_hours) % 24
        except (ValueError, IndexError):
            continue

        artist = item["track"]["artists"][0]["name"]

        if 5 <= local_hour < 12:
            time_slots["morning"].append(artist)
        elif 12 <= local_hour < 17:
            time_slots["afternoon"].append(artist)
        elif 17 <= local_hour < 22:
            time_slots["evening"].append(artist)
        else:
            time_slots["night"].append(artist)

    all_artists = {a for artists in time_slots.values() for a in artists}
    artist_tags: dict[str, list] = {}
    for artist in all_artists:
        tags_data = _lastfm.get_artist_top_tags(artist)
        artist_tags[artist] = tags_data.get("tags", [])[:5]

    def calc_mood(artists: list[str]) -> list:
        tag_counts: dict[str, int] = {}
        for artist in artists:
            for tag in artist_tags.get(artist, []):
                tag_name = tag["name"].lower()
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
        total = sum(tag_counts.values()) or 1
        return [
            {"tag": t, "weight_pct": round(c / total * 100, 1)}
            for t, c in sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
        ]

    return {
        "utc_offset_hours": utc_offset_hours,
        "mood_by_time": {
            slot: {"track_count": len(artists), "top_tags": calc_mood(artists)}
            for slot, artists in time_slots.items()
        },
    }


def traverse_track_graph(
    artist_name: str,
    track_name: str,
    hops: int = 2,
    branch: int = 4,
) -> dict:
    """
    曲から類似→類似と多段探索し「この曲から2〜3ステップ離れた未知の名曲」を発掘する。
    Last.fm の類似曲グラフを辿るため、ジャンルやムードが近い曲を広く探索できる。
    """
    visited: set[str] = set()
    frontier = [(artist_name, track_name, 0, 1.0, [f"{artist_name} — {track_name}"])]
    discoveries = []

    while frontier:
        artist, track, depth, score, path = frontier.pop(0)
        key = f"{artist.lower()}::{track.lower()}"
        if key in visited:
            continue
        visited.add(key)

        if depth > 0:
            discoveries.append({
                "artist": artist,
                "track": track,
                "depth": depth,
                "cumulative_score": round(score, 3),
                "discovery_path": " → ".join(path),
            })

        if depth < hops:
            similar = _lastfm.get_similar_tracks(artist, track, limit=branch)
            for t in similar.get("similar_tracks", []):
                next_key = f"{t['artist'].lower()}::{t['name'].lower()}"
                if next_key not in visited:
                    frontier.append((
                        t["artist"],
                        t["name"],
                        depth + 1,
                        score * t["match"],
                        path + [f"{t['artist']} — {t['name']}"],
                    ))

    discoveries.sort(key=lambda x: (x["depth"], -x["cumulative_score"]))
    return {
        "seed": f"{artist_name} — {track_name}",
        "hops": hops,
        "total_discovered": len(discoveries),
        "discoveries": discoveries[:30],
    }
