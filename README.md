# claude-spotify-tools

Claude で Spotify を操作する MCP サーバー + スキル集。再生・検索・プレイリスト管理から、Last.fm を使ったアーティスト発掘まで自然言語で動かせる。

## できること

| カテゴリ | 主な操作 |
| -------- | -------- |
| **再生** | 再生/停止、曲送り、音量・シャッフル・リピート、デバイス切替 |
| **履歴** | 最近聴いた曲、よく聴くトラック/アーティスト、ジャンル分布 |
| **検索** | 曲・アーティスト・アルバム・プレイリスト |
| **プレイリスト** | 一覧・曲の追加/削除・新規作成 |
| **ライブラリ** | 曲・アルバムの保存と取得 |
| **Last.fm** | 類似アーティスト/曲、タグ、アーティスト・アルバム情報 |
| **ディスカバリー** | 好み分析、隠れた名曲発掘、アーティストグラフ探索 |

## 必要なもの

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Spotify Developer アカウント（Client ID / Secret）
- Last.fm API キー（発掘系の機能で使用）

## セットアップ

### 1. Spotify アプリを作る

[Spotify Developer Dashboard](https://developer.spotify.com/dashboard) でアプリを作成し、Redirect URI に `http://127.0.0.1:8888/callback` を追加する。

### 2. Last.fm API キーを取得する

[Last.fm API アカウント作成](https://www.last.fm/api/account/create) でキーを発行する。Last.fm アカウントが必要（無料）。

> キーを設定しない場合、Last.fm 系のツールは `LASTFM_API_KEY が設定されていません` エラーを返す。

### 3. 依存関係をインストールする

```bash
uv sync
```

### 4. 環境変数を設定する

プロジェクトルートに `.env` を作成：

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
LASTFM_API_KEY=your_lastfm_api_key
```

### 5. 初回認証

```bash
uv run auth.py
```

ブラウザで Spotify の認証画面が開く。完了するとトークンが `.cache/token.json` に保存され、以降は自動でリフレッシュされる。

## Claude Code に登録する

### MCP サーバー

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uv",
      "args": ["--directory", "{project_directory}", "run", "main.py"]
    }
  }
}
```

### スキル

`.claude/skills/` のファイルをグローバル設定にコピーするか、このディレクトリで Claude Code を起動すると自動で読み込まれる。

スキルは自然言語でトリガーされる会話フロー。MCP ツールを組み合わせて複雑な操作を一言で実行できる。

#### アーティスト

| スキル | 何をするか | 使い方の例 |
| ------ | ---------- | ---------- |
| `artist-profile` | Spotify × Last.fm でアーティストを調査してプロフィールを提示 | 「Radiohead ってどんなアーティスト？」 |
| `artist-deep-dive` | ディスコグラフィをロードマップ化して入門〜深掘りの順番を提示・再生 | 「〇〇のアルバムどれから聴けばいい？」 |

#### リスナープロファイル

| スキル | 何をするか | 使い方の例 |
| ------ | ---------- | ---------- |
| `listener-profile` | 好みのジャンル・時間帯・聴き方のパターンをまとめて分析 | 「私ってどんなリスナー？」 |
| `recent-trends` | 直近4週間の傾向を過去と比べてレポート | 「最近どんな音楽聴いてる？」 |

#### 新しい音楽を探す

| スキル | 何をするか | 使い方の例 |
| ------ | ---------- | ---------- |
| `recommended-artist` | 聴いた曲から、まだ知らない近いアーティストを提案 | 「おすすめのアーティスト教えて」 |
| `recommended-album` | おすすめアルバムを提示してライブラリ保存まで実行 | 「今の気分に合うアルバムある？」 |
| `recommended-playlist` | 好みに合うプレイリストを探して再生 | 「いい感じのプレイリストかけて」 |
| `discovery-session` | 開拓度を診断して、今の傾向から自然につながる未知アーティストを提案 | 「新しいアーティスト開拓したい」 |

#### ジャンルを広げる

隣接（adjacent）・深掘り（deep）・冒険（explorer）の3モード × アーティスト/アルバム/プレイリストで組み合わせ自由。

| スキル | 何をするか | 使い方の例 |
| ------ | ---------- | ---------- |
| `genre-adjacent-artist` | まだあまり聴いていないジャンルへの橋渡しアーティストを提案 | 「違うジャンルだけど合いそうなの教えて」 |
| `genre-adjacent-album` | genre-adjacent で出たアーティストのアルバムを提示・保存 | 「さっきのアーティストのアルバム見たい」 |
| `genre-adjacent-playlist` | genre-adjacent の結果でプレイリストを再生 | 「隣接ジャンルでプレイリストかけて」 |
| `genre-deep-artist` | よく聴くジャンルをさらに深く掘る | 「このジャンルもっと掘りたい」 |
| `genre-deep-album` | genre-deep で出たアーティストのアルバムを提示・保存 | 「深掘りジャンルのアルバム教えて」 |
| `genre-deep-playlist` | genre-deep の結果でプレイリストを再生 | 「同じ系統でプレイリスト流して」 |
| `genre-explorer-artist` | 普段と全く違うジャンルへ思い切って飛び込む | 「真逆な感じのアーティスト教えて」 |
| `genre-explorer-album` | genre-explorer で出たアーティストのアルバムを提示・保存 | 「冒険ジャンルのアルバムを保存して」 |
| `genre-explorer-playlist` | genre-explorer の結果でプレイリストを再生 | 「対極ジャンルでプレイリストかけて」 |

#### プレイリストを探す・作る

| スキル | 何をするか | 使い方の例 |
| ------ | ---------- | ---------- |
| `vibe-playlist` | 特定のアーティスト/曲をベースに類似アーティストから新規プレイリストを作成・再生 | 「〇〇みたいな曲でプレイリスト作って」 |
| `search-playlists` | キーワードでプレイリストを検索して再生 | 「○○系のプレイリスト探して」 |
| `weather-mix` | 今いる場所の天気・時間帯からアーティストを選定し、関連アーティストも含めたプライベートプレイリストを自動作成・再生 | 「今の天気に合う曲かけて」 |

#### 曲を探す・再生する

| スキル | 何をするか | 使い方の例 |
| ------ | ---------- | ---------- |
| `search-tracks` | 曲名・アーティスト・キーワードで検索して一覧表示（再生なし）。曲名が不明な場合は Web 検索で特定してから Spotify 検索 | 「〇〇って曲ある？」「〇〇の曲を探して」 |
| `search-and-play` | 曲を検索してすぐ再生。曲名が不明な場合は Web 検索で特定してから再生まで一気に実行 | 「〇〇を流して」「〇〇かけて」 |

## プロジェクト構成

```text
claude-spotify-tools/
├── main.py          # MCPサーバー起動・ツール登録
├── auth.py          # OAuth認証・トークン管理
├── client.py        # Spotify API クライアント
├── tools/
│   ├── playback.py  # 再生操作・デバイス管理
│   ├── history.py   # 履歴・トップ曲/アーティスト
│   ├── search.py    # 検索
│   ├── playlist.py  # プレイリスト管理
│   ├── library.py   # ライブラリ操作
│   ├── lastfm.py    # Last.fm API
│   └── discovery.py # 音楽探索・分析
└── pyproject.toml
```

## 使用例

```text
「今の曲を止めて」
→ pause()

「過去6ヶ月でよく聴いた曲トップ5は？」
→ get_top_tracks(time_range="medium_term", limit=5)

「このアーティストに似た人教えて」
→ get_similar_artists(artist="...")
```
