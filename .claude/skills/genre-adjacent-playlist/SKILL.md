---
name: genre-adjacent-playlist
description: genre-adjacent分析で発掘したギャップジャンルのブリッジアーティストをもとにSpotifyプレイリストを作成し再生する。「genre-adjacentで上がったアーティストをプレイリストにして」「さっきのアーティストでプレイリスト作って再生して」「ジャンル探索プレイリスト作って」「ブリッジアーティストをまとめて聴きたい」など、genre-adjacent推薦結果のプレイリスト化・再生を求められたときは必ずこのスキルを使う。genre-adjacentの推薦が会話に既にある場合はその結果を再利用し、ない場合はgenre-adjacentスキルを先に実行してからこのスキルを続ける。
---

# genre-adjacent-playlist

genre-adjacent で発掘したブリッジアーティストの代表曲でプレイリストを作り、そのまま再生する。

## 前提確認

会話に genre-adjacent の推薦結果が既にあれば **Step 2 から始める**。
結果がない場合は genre-adjacent スキルを先に実行し、推薦リストを得てから Step 2 へ進む。

---

## Step 1: アーティストリストを確定する

会話中の genre-adjacent 推薦から以下を抽出する：
- アーティスト名（3〜5人）
- 対応するギャップジャンル名（プレイリスト名に使う）

---

## Step 2: 各アーティストの代表曲を収集する（並行実行）

各アーティストについて `search_tracks` を同時実行する。

```
query: "artist:{アーティスト名}"
limit: 3
```

- 1アーティストにつき上位2〜3曲を選ぶ
- track URI（`spotify:track:...`）をリストアップする
- アーティスト数は **ジャンルごとに3〜4人、合計9〜12人** を目安にする

> 複数アーティストの検索は必ず並行（同一ターン内で複数ツール呼び出し）で行い、逐次実行しない。

---

## Step 3: プレイリストを作成する

```
create_playlist(
  name="ジャンル探索: {ギャップジャンル名}",
  description="genre-adjacent で発掘したブリッジアーティスト集。{アーティスト名をカンマ区切り}"
)
```

返ってきた playlist_id を保持する。

---

## Step 4: 収集した曲をプレイリストに追加する

Step 2 で集めた track URI をすべて `add_tracks_to_playlist` で一括追加する。

```
add_tracks_to_playlist(
  playlist_id=<Step 3 で取得>,
  track_uris=[<Step 2 で収集した全 URI>]
)
```

---

## Step 5: プレイリストを再生する

`play_context` でプレイリストを再生開始する。

```
play_context(context_uri="spotify:playlist:{playlist_id}")
```

---

## Step 6: 完了を伝える

以下のフォーマットで報告する：

```
プレイリスト「ジャンル探索: {ギャップジャンル名}」を作成して再生を開始しました。

収録アーティスト：
- {アーティスト名}: {曲名}, {曲名}
- ...

合計 {N} 曲 / {アーティスト数} アーティスト

気に入ったアーティストがいればアルバム一覧を見ることもできます。
```

---

## 注意点

- **プレイリストは必ず private で作成する**（`create_playlist` のデフォルトは private だが明示的に意識すること）
- `search_tracks` で曲が見つからない場合は `search_artists` でアーティストURIを取得し `play_context` でアーティスト自体を再生して代替する
- プレイリスト名が重複しても気にせず新規作成してよい（Spotifyは同名を許容する）
- Step 2〜4 の間にユーザーへの確認は不要。一気に実行する
