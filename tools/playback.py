from typing import Literal

import client


def play() -> dict:
    """再生を再開する"""
    return client.api_put("/me/player/play")


def pause() -> dict:
    """再生を一時停止する"""
    return client.api_put("/me/player/pause")


def next_track() -> dict:
    """次の曲にスキップする"""
    return client.api_post("/me/player/next")


def previous_track() -> dict:
    """前の曲に戻る"""
    return client.api_post("/me/player/previous")


def play_track(uri: str) -> dict:
    """指定した Spotify URI の曲を再生する (例: spotify:track:xxx)"""
    return client.api_put("/me/player/play", {"uris": [uri]})


def play_context(uri: str) -> dict:
    """アルバム・プレイリスト・アーティストを再生する (例: spotify:album:xxx / spotify:playlist:xxx / spotify:artist:xxx)"""
    return client.api_put("/me/player/play", {"context_uri": uri})


def set_volume(volume: int) -> dict:
    """音量を設定する (0-100)"""
    return client.api_put(f"/me/player/volume?volume_percent={volume}")


def set_shuffle(state: bool) -> dict:
    """シャッフルの ON/OFF を切り替える"""
    return client.api_put(f"/me/player/shuffle?state={str(state).lower()}")


def set_repeat(mode: Literal["off", "track", "context"]) -> dict:
    """リピートモードを設定する: off / track (1曲リピート) / context (プレイリストリピート)"""
    return client.api_put(f"/me/player/repeat?state={mode}")


def get_current_track() -> dict:
    """現在再生中の曲情報を返す"""
    return client.api_get("/me/player/currently-playing")


def get_devices() -> dict:
    """利用可能な Spotify デバイス一覧を返す"""
    return client.api_get("/me/player/devices")


def transfer_playback(device_id: str) -> dict:
    """再生を指定デバイスに移す。device_id は get_devices で確認できる"""
    return client.api_put("/me/player", {"device_ids": [device_id]})


def add_to_queue(uri: str) -> dict:
    """曲を再生キューに追加する (例: spotify:track:xxx)"""
    return client.api_post(f"/me/player/queue?uri={uri}")
