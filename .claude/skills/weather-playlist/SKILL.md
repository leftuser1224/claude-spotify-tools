---
name: weather-playlist
description: ユーザーが場所（都市名）を伝えると、その場所の現在の天気と時間帯を自動取得し、ムードに合った既存のSpotify公開プレイリストを検索して再生する。「今の天気に合う曲かけて」「東京の今の気分でプレイリスト選んで」「雨の日に合うBGM流して」「場所と時間と天気でいい感じのプレイリスト」「今いる場所の天気で音楽かけて」などの要求が来たら必ずこのスキルを使う。場所さえ分かれば天気・時刻はAPIから自動取得するので、ユーザーに天気を聞く必要はない。
---

# weather-playlist

場所の現在天気と時間帯からムードを判断し、Spotifyの公開プレイリストを探して再生する。

## 手順

### 1. 場所を確認する

プロンプトに場所が含まれていれば使用。なければユーザーに「今どこにいますか？」と聞く。
都市名なら英語・日本語どちらでもよい（例: 東京、Tokyo、Osaka、New York）。

---

### 2. 天気と現地時刻を取得する

`WebFetch` で wttr.in を呼ぶ（APIキー不要）：

```
URL: https://wttr.in/{location}?format=j1
```

WebFetch の prompt には以下を指定する：
```
Extract these exact fields from the JSON:
1. current_condition[0].weatherDesc[0].value
2. current_condition[0].temp_C
3. current_condition[0].localObsDateTime  ← this is LOCAL time (format: "2026-06-06 14:30")
4. If localObsDateTime is missing or empty, extract current_condition[0].observation_time and note it is UTC.
Return all four values clearly labeled.
```

レスポンスから以下を読み取る：
- `current_condition[0].weatherDesc[0].value` — 天気（Sunny / Partly cloudy / Overcast / Light rain / Rain / Snow / Fog 等）
- `current_condition[0].temp_C` — 気温（℃）
- **現地時刻の取得（優先順）：**
  1. `localObsDateTime` が存在すればそのまま現地時刻として使う（例: `"2026-06-06 14:30"`）
  2. `localObsDateTime` が空・欠損の場合は `observation_time` を取得する。**これはUTC表記**なので、都市のUTCオフセットを加算してローカル時刻に変換する。
     - 主なオフセット例：日本(JST)=+9h、韓国(KST)=+9h、中国(CST)=+8h、インド(IST)=+5:30h、英国(BST/GMT)=+1/0h、米東部(EDT/EST)=-4/-5h、米西部(PDT/PST)=-7/-8h
     - 例：`observation_time = "03:27 AM"` + 日本(+9h) → `12:27 PM` = 昼

> 失敗した場合：ユーザーに天気と現在時刻を直接聞き、Step 3 へ進む。

---

### 3. ムードキーワードを決める

**時間帯・天気・季節** の3軸を組み合わせてキーワードを3セット作る。

#### 時間帯の区分
| 区分 | 時間 |
|---|---|
| morning | 5〜10時 |
| midday | 10〜14時 |
| afternoon | 14〜18時 |
| evening | 18〜21時 |
| night | 21〜24時 |
| late night | 0〜5時 |

#### 天気グループ
| 天気の説明 | グループ |
|---|---|
| Sunny / Clear / Mostly sunny | sunny |
| Partly cloudy / Overcast / Cloudy | cloudy |
| Light rain / Rain / Drizzle / Showers | rainy |
| Snow / Blizzard / Sleet | snowy |
| Fog / Mist | foggy |
| Thunderstorm / Heavy rain | stormy |

#### 季節の決め方

現在の月と場所の半球から季節を判定する：

| 月 | 北半球 | 南半球 |
|---|---|---|
| 3〜5月 | spring | autumn |
| 6〜8月 | summer | winter |
| 9〜11月 | autumn | spring |
| 12〜2月 | winter | summer |

> 南半球の都市（シドニー、ブエノスアイレス、ケープタウン等）は北半球と逆になる。

季節をキーワードに反映する例：
- spring → "spring playlist", "cherry blossom", "spring drive"
- summer → "summer vibes", "beach playlist", "summer nights"
- autumn → "autumn chill", "fall playlist", "cozy autumn"
- winter → "winter playlist", "cozy winter", "holiday warm"

#### 気温補正
- 30°C 以上 → "summer heat" / "tropical" を追加
- 5°C 以下 → "cold day" / "freezing" を追加（冬のキーワードを強める）

#### キーワード合成の考え方

天気 × 時間帯 × 季節の3要素を組み合わせて、検索クエリとして自然なフレーズにする。

例：
- 晴れ・夏・朝 → "summer morning vibes" / "sunny summer morning" / "beach morning playlist"
- 雨・秋・夜 → "autumn rainy night" / "fall rain chill" / "rainy night cozy"
- 曇り・春・午後 → "spring afternoon chill" / "cloudy spring day" / "mellow spring playlist"
- 雪・冬・夕方 → "winter evening cozy" / "snowfall evening" / "winter sunset playlist"

季節感が薄い天気（雨・霧など）の場合は季節キーワードを添えると検索精度が上がる。
逆に夏の晴れのように天気と季節が重なる場合は、どちらか一方を強調すれば十分。

キーワードは固定テーブルに縛られず、状況に応じてより自然な言葉を使ってよい。
日本語圏でも英語キーワードの方がSpotifyで幅広く引っかかるので英語を優先。

---

### 4. プレイリストを並行検索する

Step 3 で決めた3キーワードを**同時に**検索する：

```
search_playlists(query="<キーワード1>", limit=8)
search_playlists(query="<キーワード2>", limit=8)
search_playlists(query="<キーワード3>", limit=8)
```

---

### 5. 候補を絞って提示する

3つの検索結果を合算し、重複を除いた上で上位3〜4件を選ぶ。

選ぶ基準（優先順）：
1. プレイリスト名がムードと一致している
2. フォロワー数が多い（人気プレイリスト優先）
3. 曲数が極端に少なくない（10曲以上）

**出力フォーマット：**

```
## [場所]の今にぴったりなプレイリスト

📍 [場所] ／ 🌦️ [天気]、[気温]°C ／ 🕐 現地時刻 [時刻]

気分のキーワード: [ムードのひとこと。例：「雨の夕方、静かにこもりたい感じ」]

1. **[プレイリスト名]**（[フォロワー数]人がフォロー）
   → [なぜこのムードに合うか一言]

2. **[プレイリスト名]**
   → ...

3. **[プレイリスト名]**
   → ...

---
番号で選んでください。「もっとアップテンポに」「日本語の曲で」などもOKです。
```

---

### 6. 再生する

ユーザーが番号または「流して」と言ったら、対応するプレイリストを再生する：

```
play_context(context_uri="spotify:playlist:{playlist_id}")
```

---

## 追加要望への対応

- **「もっと静かなの」「激しめに」**: キーワードを変えて Step 4 から再検索
- **「日本語の曲で」**: クエリに "japanese" / "j-pop" / "j-indie" を加えて再検索
- **「別のにして」**: 次の候補を提示するか再検索
- **「保存して」**: `save_track` や `add_tracks_to_playlist` で対応

## 注意点

- wttr.in は都市名をURLに入れるだけで動く（例: `https://wttr.in/Tokyo?format=j1`）。スペースは `+` に置換（New+York）
- 日本語地名はそのまま使えることが多いが、英語の方が安定する
- 検索結果にユーザーの非公開プレイリストは出てこない（公開プレイリストのみ）
- プレイリストが全く見つからない場合は別キーワードで再検索する
