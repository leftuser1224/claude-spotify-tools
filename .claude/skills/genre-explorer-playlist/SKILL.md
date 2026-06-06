---
name: genre-explorer-playlist
description: genre-explorer分析で発掘した対極ジャンルの入口アーティストをもとにSpotifyプレイリストを作成し再生する。「genre-explorerで上がったアーティストをプレイリストにして」「さっきの冒険ジャンルでプレイリスト作って」「対極ジャンル探索プレイリスト作って」「ガラッと変えた結果をまとめて聴きたい」など、genre-explorer推薦結果のプレイリスト化・再生を求められたときは必ずこのスキルを使う。genre-explorerの推薦が会話に既にある場合はその結果を再利用し、ない場合はgenre-explorerスキルを先に実行してからこのスキルを続ける。
---

# genre-explorer-playlist

genre-explorer で発掘した対極ジャンルの入口アーティストの代表曲でプレイリストを作り、そのまま再生する。

## 前提確認

会話に genre-explorer の推薦結果が既にあれば **Step 2 から始める**。
結果がない場合は genre-explorer スキルを先に実行し、推薦リストを得てから Step 2 へ進む。

---

## Step 1: アーティストリストを確定する

会話中の genre-explorer 推薦から以下を抽出する：
- アーティスト名（3〜5人）
- 対極ジャンル名（プレイリスト名に使う）

---

## Step 2: 各アーティストの代表曲を収集する（並行実行）

各アーティストについて `search_tracks` を同時実行する。

```
query: "artist:{アーティスト名}"
limit: 5
```

- 1アーティストにつき上位3曲を選ぶ
- track URI（`spotify:track:...`）をリストアップする
- アーティスト数を **10〜12人を目安に、各3曲で合計30曲** を集める

> 複数アーティストの検索は必ず並行（同一ターン内で複数ツール呼び出し）で行い、逐次実行しない。

---

## Step 3: プレイリストを作成する

```
create_playlist(
  name="ジャンル冒険: {対極ジャンル名}",
  description="genre-explorer で発掘した対極ジャンルの入口アーティスト集。{アーティスト名をカンマ区切り}"
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

```
play_context(context_uri="spotify:playlist:{playlist_id}")
```

---

## Step 6: 完了を伝える

```
プレイリスト「ジャンル冒険: {対極ジャンル名}」を作成して再生を開始しました。

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
- プレイリスト名が重複しても気にせず新規作成してよい
- Step 2〜4 の間にユーザーへの確認は不要。一気に実行する
