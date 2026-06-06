import client


def save_track(track_id: str) -> dict:
    """曲をお気に入り（ライブラリ）に追加する。track_id は URI の末尾部分 (spotify:track:XXX の XXX)"""
    return client.api_put("/me/tracks", {"ids": [track_id]})


def unsave_track(track_id: str) -> dict:
    """曲をお気に入り（ライブラリ）から削除する"""
    return client.api_delete("/me/tracks", {"ids": [track_id]})


def get_saved_tracks(limit: int = 20) -> dict:
    """お気に入りの曲一覧を返す"""
    return client.api_get(f"/me/tracks?limit={limit}")


def save_album(album_id: str) -> dict:
    """アルバムをライブラリに保存する。album_id は URI の末尾部分 (spotify:album:XXX の XXX)"""
    return client.api_put("/me/albums", {"ids": [album_id]})


def get_saved_albums(limit: int = 20) -> dict:
    """ライブラリに保存したアルバム一覧を返す"""
    return client.api_get(f"/me/albums?limit={limit}")


def get_artist_albums(artist_id: str, limit: int = 10) -> dict:
    """アーティストのアルバム一覧を返す。artist_id は URI の末尾部分 (spotify:artist:XXX の XXX)"""
    return client.api_get(f"/artists/{artist_id}/albums?include_groups=album,single&limit={limit}")
