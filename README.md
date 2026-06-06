# claude-spotify-tools

Spotify × Last.fm の MCP サーバーおよびスキル。Claude から音楽再生・履歴確認・プレイリスト管理・アーティスト探索などを自然言語で操作できる。

## 機能

| カテゴリ | 主なツール |
| -------- | ----------- |
| **再生操作** | 再生/一時停止、曲送り/戻し、音量・シャッフル・リピート設定、デバイス切替 |
| **再生履歴** | 最近再生した曲、トップトラック/アーティスト（期間指定）、ジャンルプロファイル |
| **検索** | 曲・アーティスト・アルバム・プレイリスト検索 |
| **プレイリスト** | 一覧取得、曲の追加/削除、新規作成 |
| **ライブラリ** | 曲・アルバムの保存/取得、アーティストのアルバム取得 |
| **Last.fm** | 類似アーティスト/曲、タグ、アーティスト・アルバム情報 |
| **ディスカバリー** | テイストプロファイル構築、隠れた名曲発掘、アーティストグラフ探索、気分分析 |

## 前提条件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Spotify Developer アカウント（Client ID / Client Secret）
- Last.fm API キー（Last.fm ツール使用時）

## セットアップ

### 1. Spotify アプリの作成

[Spotify Developer Dashboard](https://developer.spotify.com/dashboard) でアプリを作成し、Redirect URI に `.env` で設定した `SPOTIFY_REDIRECT_URI`（デフォルト: `http://127.0.0.1:8888/callback`）を追加する。

### 2. Last.fm API キーの取得

[Last.fm API アカウント作成ページ](https://www.last.fm/api/account/create) でアプリを登録し、API キーを取得する。Last.fm アカウントが必要（無料）。

> Last.fm API キーは `lastfm.py` のすべてのツールおよび `discovery.py` の音楽探索機能で使用される。設定しない場合、これらのツールは `LASTFM_API_KEY が設定されていません` エラーを返す。

### 3. 依存パッケージのインストール

```bash
uv sync
```

### 3. 環境変数の設定

`.env` ファイルをプロジェクトルートに作成：

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback  # 省略時はこのデフォルト値が使われる
LASTFM_API_KEY=your_lastfm_api_key  # Last.fm ツール使用時
```

### 4. 初回認証

```bash
uv run auth.py
```

ブラウザが開き Spotify の認証画面が表示される。認証後、トークンが `.cache/token.json` に保存される（`.gitignore` 済み）。以降は自動でリフレッシュされる。

## Claude Code への登録

### 1. MCP サーバーの登録

`~/.claude/claude_desktop_config.json` に追記：

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

### 2. スキルの登録

`.claude/skills/` 配下のスキルファイルをグローバル設定にコピーするか、このプロジェクトディレクトリで Claude Code を起動することで自動的に読み込まれる。

スキルは自然言語でトリガーされる高レベルな会話フロー。MCP ツールを組み合わせて複雑な操作を一言で実行できる。

| スキル | 説明 | トリガー例 |
| ------ | ---- | --------- |
| `artist-deep-dive` | アーティストのディスコグラフィをロードマップ化して「どのアルバムからどう聴くか」を提示・再生 | 「〇〇のアルバムどれから聴けばいい？」 |
| `artist-profile` | アーティストを Spotify × Last.fm で多角的に調査 | 「Radiohead ってどんなアーティスト？」 |
| `discovery-session` | 開拓度スコアを診断し、聴取傾向から自然につながる未知のアーティストを文脈付きで提案 | 「新しいアーティスト開拓したい」 |
| `listener-profile` | 自分の聴取傾向を多角的に分析 | 「私ってどんなリスナー？」 |
| `recent-trends` | 直近4週間の聴取傾向を過去と比較 | 「最近どんな音楽聴いてる？」 |
| `recommended-artist` | 聴取履歴から未探索の近似アーティストを推薦 | 「おすすめのアーティスト教えて」 |
| `recommended-album` | おすすめアルバムを提示・ライブラリ保存まで実行 | 「今の気分に合うアルバムある？」 |
| `recommended-playlist` | 好みに合うプレイリストを検索・再生 | 「いい感じのプレイリストかけて」 |
| `genre-adjacent-artist` | 聴取が少ないジャンルへの「橋渡し」アーティストを発掘 | 「違うジャンルだけど合いそうなの教えて」 |
| `genre-adjacent-album` | genre-adjacent の結果からアルバムを提示・保存 | 「さっきのアーティストのアルバム見たい」 |
| `genre-adjacent-playlist` | genre-adjacent の結果からプレイリストを再生 | 「隣接ジャンルでプレイリストかけて」 |
| `genre-deep-artist` | すでによく聴くジャンルをさらに深掘り | 「このジャンルもっと掘りたい」 |
| `genre-deep-album` | genre-deep の結果からアルバムを提示・保存 | 「深掘りジャンルのアルバム教えて」 |
| `genre-deep-playlist` | genre-deep の結果からプレイリストを再生 | 「同じ系統でプレイリスト流して」 |
| `genre-explorer-artist` | 聴取履歴と全く異なるジャンルへの冒険 | 「真逆な感じのアーティスト教えて」 |
| `genre-explorer-album` | genre-explorer の結果からアルバムを提示・保存 | 「冒険ジャンルのアルバムを保存して」 |
| `genre-explorer-playlist` | genre-explorer の結果からプレイリストを再生 | 「対極ジャンルでプレイリストかけて」 |
| `search-playlists` | キーワードでプレイリストを検索・再生 | 「○○系のプレイリスト探して」 |
| `weather-playlist` | 現在地の天気・時間帯に合うプレイリストを自動選曲 | 「今の天気に合う曲かけて」 |

## プロジェクト構成

```text
claude-spotify-tools/
├── main.py          # FastMCP サーバー起動・ツール登録
├── auth.py          # OAuth 認証・トークン管理
├── client.py        # Spotify API 共通クライアント
├── tools/
│   ├── playback.py  # 再生操作・デバイス管理
│   ├── history.py   # 履歴・トップ曲・アーティスト
│   ├── search.py    # 検索
│   ├── playlist.py  # プレイリスト管理
│   ├── library.py   # ライブラリ操作
│   ├── lastfm.py    # Last.fm API 連携
│   └── discovery.py # 音楽探索・分析
└── pyproject.toml
```

## 使用例

```text
「今の曲を一時停止して」
→ pause() を呼び出し PUT /me/player/pause

「過去6ヶ月でよく聴いた曲トップ5は？」
→ get_top_tracks(time_range="medium", limit=5)

「このアーティストに似たアーティストを教えて」
→ get_similar_artists(artist="...")
```
