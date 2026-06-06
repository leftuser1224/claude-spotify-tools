---
name: genre-adjacent-artist
description: ユーザーの聴取履歴でウェイトが低い・または不在のジャンルから、趣味に音楽的につながる「橋渡し」アーティストを発掘する。「普段聴かないジャンルを試したい」「あまり効かないジャンルのアーティストおすすめして」「ジャンルを広げたい」「違うジャンルだけど合いそうなの教えて」「いつもと違う感じの音楽が聴きたい」など、ジャンルの多様化・新ゾーン開拓を求める場合に必ずこのスキルを使う。recommended-musiciansとの違いは「好みの類似アーティスト」ではなく「ジャンルギャップへの入口」を提示する点。
---

# genre-adjacent-artist

ユーザーの趣味プロファイルにある「ジャンルの空白域」を特定し、そこへ自然につながる橋渡しアーティストを見つける。
「完全に離れているのは嫌だが、いつもと違うゾーンを試したい」という探索欲に応えるスキル。

## 手順

### 1. プロファイルと変化を把握（並行実行）

- `build_taste_profile(time_range="long")` — ジャンル比率（%付き）とアーティスト一覧
- `analyze_listening_evolution()` — rising/consistent/fadingでトレンドを把握
- `get_top_artists(time_range="long", limit=30)` — ランダム抽出用の30人プール

### 2. アーティストグラフでジャンルギャップを動的に特定する

`artist_profiles` の上位30人の中から **ランダムに5人抽出** し、起点として **並行で** `traverse_artist_graph` を実行する：

```
traverse_artist_graph(artist_name=<random_artist_1>, hops=1, branch=4)
traverse_artist_graph(artist_name=<random_artist_2>, hops=1, branch=4)
traverse_artist_graph(artist_name=<random_artist_3>, hops=1, branch=4)
traverse_artist_graph(artist_name=<random_artist_4>, hops=1, branch=4)
traverse_artist_graph(artist_name=<random_artist_5>, hops=1, branch=4)
```

次に、depth=2 で発見されたアーティストに対して `get_artist_top_tags` を呼び、ジャンルタグを収集する。

収集したタグのうち **`genre_breakdown` に登場しないもの** を集計し、出現頻度の高い順に並べる。
それが **ギャップジャンル候補** となる。

候補の中から **1〜2つに絞る**。広げすぎると焦点がぼける。

### 3. ジャンルブリッジを辿る

```
genre_bridge(source_genre=<支配的ジャンル>, target_genre=<ギャップジャンル>)
```

ブリッジが存在すれば連鎖ジャンルパスが得られる。これがアーティスト推薦の文脈になる。
ブリッジが見つからない場合は別のギャップジャンルを試す。

### 4. ギャップジャンルのアーティストを発掘（並行実行）

以下3つを**同時に**実行し、候補プールを作る：

**① タグ上位**：
```
get_tag_top_artists(tag=<ギャップジャンル>)
```

**② グラフ探索**（ブリッジアーティストを起点）：
```
traverse_artist_graph(artist_name=<genre_bridgeで見つかった代表アーティスト>, hops=1, branch=5)
```

**③ 隠れた候補**：
```
find_hidden_gems(min_listeners=50000, max_listeners=500000)
```

3ソースの結果を合算し、除外リストを適用した残りを候補プールとする。
候補に対して `get_artist_top_tags` でタグを確認し、本当にギャップジャンルに属するか検証する。

### 5. 除外ルール

以下はすべて推薦しない：
- `analyze_listening_evolution` の consistent / rising / fading に含まれるアーティスト
- ユーザーの上位アーティストリストに含まれるアーティスト

### 6. 出力フォーマット

```
## [ギャップジャンル名]への入口

あなたは普段 **[支配的ジャンル]** をよく聴いていますが、
**[ギャップジャンル]** はほぼ聴いていません。
[ブリッジの説明：どうつながっているか1〜2文。例：「[支配的ジャンル]が[中間ジャンル]を経て[ギャップジャンル]へと音楽的につながっています」]

1. **[アーティスト名]**
   ジャンル: [タグ]
   → [なぜ橋渡しとして合うか1〜2文。あなたの好みのどの要素と重なるかを具体的に]

...（3〜5人）

---
気になる人がいたら流します。アルバム一覧を見ることもできます。
```

### 7. 再生オファー

- 選ばれたら `search_artists` でURIを確認 → `play_context` でアーティスト再生
- 「アルバム見たい」なら `search_artists` でID取得 → `get_artist_albums`

## 注意点

- **完全に離れたジャンル（jazz, classical, hip-hop, electronic dance等）は推薦しない**。あくまで「ロック系・インディ系・J-ロック系の隣接地帯」に留まる
- ギャップジャンルが見当たらない場合は「実はかなり幅広く聴いています」と正直に伝え、より細かいサブジャンル（例：britpopの中でも madchester 系）を提案する
- プロンプトに「〇〇系は嫌」がある場合はそのジャンルを除外して別のブリッジを探す
