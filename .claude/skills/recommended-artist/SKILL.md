---
name: recommended-musicians
description: ユーザーのSpotify試聴履歴（過去1年）を分析し、趣味と近いが普段あまり聴いていない未探索のアーティストをレコメンドする。「おすすめのアーティスト教えて」「新しいアーティスト発見したい」「知らないけど好みそうな人いない？」「〇〇みたいなアーティストいる？」など、アーティスト推薦を求められたときは必ずこのスキルを使う。
---

# recommended-musicians

Spotify聴取データ × Last.fm音楽グラフを使って、**聴取履歴にない・かつ音楽的に近い**アーティストを見つける。キーワード検索ではなく類似グラフを辿るため、表面的な検索では出てこない本質的に近いアーティストが発掘できる。

## 手順

### 1. 好みの把握（並行実行）

- `build_taste_profile(time_range="long")` — ジャンル比率（%付き）＋上位20アーティストのLast.fmタグ
- `get_recently_played(limit=50)` — 直近再生（除外リスト用）
- `analyze_listening_evolution()` — `consistent`（常連）と `rising`（最近浮上）を把握

### 2. 好みの軸を読み取る

`build_taste_profile` の `genre_breakdown` から以下を整理する：

| 軸 | 読み取り方 |
|---|---|
| **メインジャンル** | weight_pct 上位のタグをマクロジャンルに束ねる |
| **地域** | british/japanese/irish/australian等のタグから |
| **規模感** | 上位アーティストのLast.fm listenerを参考に「よく聴くアーティストの典型的なリスナー数帯」を把握 |

### 3. 未探索アーティストを探す

**メインアプローチ：`find_hidden_gems`**

```
find_hidden_gems(
    min_listeners=<よく聴くアーティストのリスナー数の半分>,
    max_listeners=<よく聴くアーティストのリスナー数の2倍>,
    limit=15,
    time_range="long"
)
```

このツールは：上位アーティストのLast.fm類似アーティストを辿り → 聴取履歴にいないものだけ → 指定リスナー数範囲内に絞る。キーワード検索より精度が高い。

プロンプトに「もっとマイナーな」があれば `max_listeners` を下げる、「有名どころで」なら `min_listeners` を上げる。

**補助アプローチ：`traverse_artist_graph`（プロンプトに「意外な」「遠い領域」があるとき）**

```
traverse_artist_graph(artist_name=<常連アーティスト>, hops=2, branch=4)
```

2ホップ先まで辿って「好みの2〜3ステップ離れた未知領域」を探す。

### 4. 候補の検証

`find_hidden_gems` で得た候補のうち気になるものは `get_artist_top_tags` でジャンルを確認し、本当に好みに合っているか補強する。

### 5. 出力フォーマット

```
## おすすめアーティスト（未探索枠）

1. **[アーティスト名]**
   Last.fm リスナー: [数]人 / ジャンル: [タグ]
   [名前]に似ている（match: XX%）
   → [なぜ合うか：ジャンル・地域・規模感を1〜2文で]

...（5人）

---
気になる人がいたら流します。アルバム一覧を見ることもできます。
```

### 6. 再生オファー

- 選ばれたら `search_artists` でURIを確認 → `play_context` でアーティスト再生
- 「アルバム見たい」なら `search_artists` でID取得 → `get_artist_albums`

## ポイント

- 除外：`analyze_listening_evolution` の `consistent` / `rising` / `fading` に含まれるアーティストは推薦しない
- 有名アーティストも対象に含めてよい（リスナー数の上限なし）
- プロンプトに「〇〇みたいな」「〇〇系」があればそのアーティストを `traverse_artist_graph` の起点にする
- プロンプトに気分・シチュエーションがあればジャンルフィルターの優先軸にする
