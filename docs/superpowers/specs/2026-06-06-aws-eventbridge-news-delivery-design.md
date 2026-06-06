# AWS EventBridge 定時ニュース配信システム 設計書

## 概要

毎朝6時（JST）に複数の技術ニュースソースを収集し、Claude API でカテゴリ別ダイジェストに整理して、メールで配信するシステム。macOS launchd の代替として AWS EventBridge を使用し、クラウド上で完結する構成。

## アーキテクチャ

```
EventBridge Rule (cron: 毎朝 JST 6:00)
    │
    ▼
Lambda Function (Python 3.12, タイムアウト5分)
    ├─ 1. フェッチフェーズ（AI不使用）
    │      ├─ Qiita RSS
    │      ├─ Zenn RSS
    │      ├─ はてなブックマーク RSS
    │      ├─ Hacker News API
    │      ├─ Reddit JSON API
    │      └─ YouTube RSS
    │
    ├─ 2. Claude API 呼び出し（1回/日）
    │
    └─ 3. SES メール送信
```

## コンポーネント詳細

### Lambda 関数

- **ランタイム:** Python 3.12
- **タイムアウト:** 5分
- **メモリ:** 512MB（デフォルトで十分）
- **依存ライブラリ:** `anthropic`, `requests`

### フェッチャー（各ソース）

各フェッチャーは独立した try/except で囲まれており、1ソースの失敗が全体に影響しない。

| ソース | 取得方法 | URL / API |
|--------|----------|-----------|
| Qiita | RSS (Atom) | `https://qiita.com/popular-items/feed.atom` |
| Zenn | RSS | `https://zenn.dev/feed` |
| はてなブックマーク | RSS | `https://b.hatena.ne.jp/hotentry/it.rss` |
| Hacker News | JSON API | `https://hacker-news.firebaseio.com/v0/topstories.json` |
| Reddit | JSON API | `https://www.reddit.com/r/{subreddit}.json` |
| YouTube | RSS (XML) | `https://www.youtube.com/feeds/videos.xml?channel_id={id}` |
| X/Twitter | Tavily Search API | `site:twitter.com` クエリで SEARCH_KEYWORDS を検索（1リクエスト/日） |
| キーワードニュース | Tavily Search API | SEARCH_KEYWORDS を1件ずつ検索（キーワード数リクエスト/日） |

各フェッチャーの返却形式:
```python
[{"source": str, "title": str, "url": str, "description": str}]
```

### Claude API 呼び出し（summarizer.py）

- **モデル:** `claude-haiku-4-5-20251001`（環境変数 `CLAUDE_MODEL` で上書き可能）
- **呼び出し回数:** 1回/日
- **入力:** 全ソースの記事リスト（タイトル + URL + 説明のみ）
- **出力:** カテゴリ別日本語ダイジェスト（HTML メール形式）
- **カテゴリ:** AI/ML、Web開発、インフラ、セキュリティ、その他

**トークン見積もり（MAX_ITEMS_PER_SOURCE=10、8ソース）:**
- 入力: 約 8,000 トークン
- 出力: 約 1,500 トークン
- 月額コスト: 約 $0.12（Haiku 料金）

**Tavily 無料枠の消費:**
- 1日あたり: X検索1リクエスト + キーワード6リクエスト = 7リクエスト/日
- 月30日: 約210リクエスト（無料枠1,000件の範囲内）

### メール送信（mailer.py）

- **サービス:** Amazon SES
- **形式:** HTML メール
- **送信元:** 環境変数 `SES_FROM_ADDRESS`
- **宛先:** 環境変数 `TO_ADDRESSES`（カンマ区切りで複数指定可）

### エラーハンドリング

- 各フェッチャーは独立して失敗可能（残りのソースで処理続行）
- フェッチ結果が0件の場合はメール送信をスキップ、CloudWatch Logs にワーニング記録
- SES 送信失敗は例外を raise → Lambda エラーとして CloudWatch に記録

## インフラ構成（AWS CDK）

### ディレクトリ構成

```
colnews/
├── cdk/
│   ├── app.py                  # CDK エントリポイント
│   └── colnews_stack.py        # スタック定義
├── src/
│   ├── handler.py              # Lambda ハンドラ
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── qiita.py
│   │   ├── zenn.py
│   │   ├── hatena.py
│   │   ├── hackernews.py
│   │   ├── reddit.py
│   │   ├── youtube.py
│   │   ├── x_twitter.py        # Tavily 経由で X 投稿を検索
│   │   └── keyword_news.py     # Tavily 経由でキーワードニュースを検索
│   ├── summarizer.py
│   ├── mailer.py
│   └── requirements.txt
├── cdk.json
└── requirements.txt
```

### CDK が作成するリソース

| リソース | 詳細 |
|----------|------|
| `aws_lambda.Function` | Python 3.12、環境変数注入、タイムアウト5分 |
| `aws_events.Rule` | `cron(0 21 * * ? *)` (UTC 21:00 = JST 6:00) |
| `aws_events_targets.LambdaFunction` | EventBridge → Lambda のターゲット |
| IAM ロール | SES 送信権限、Secrets Manager 読み取り権限 |

### 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `ANTHROPIC_API_KEY` | Secrets Manager から注入 | — |
| `SES_FROM_ADDRESS` | 送信元メールアドレス | — |
| `TO_ADDRESSES` | 宛先（カンマ区切り） | — |
| `MAX_ITEMS_PER_SOURCE` | ソースあたりの最大記事数 | `10` |
| `CLAUDE_MODEL` | 使用モデル ID | `claude-haiku-4-5-20251001` |
| `YOUTUBE_CHANNEL_IDS` | 対象チャンネル ID（カンマ区切り） | — |
| `REDDIT_SUBREDDITS` | 対象サブレディット（カンマ区切り） | `programming,tech` |
| `TAVILY_API_KEY` | Secrets Manager から注入 | — |
| `SEARCH_KEYWORDS` | 検索キーワード（カンマ区切り） | `AI,LLM,AWS,TypeScript,Claude,Gemini` |

## 前提条件

- AWS アカウントで SES のサンドボックス解除済み（または送受信アドレスが検証済み）
- CDK ブートストラップ済み（`cdk bootstrap`）
- `ANTHROPIC_API_KEY` を AWS Secrets Manager に登録済み
- `TAVILY_API_KEY` を AWS Secrets Manager に登録済み（Tavily アカウント作成・API キー取得済み）

## テスト方針

- 各フェッチャーは単体テスト可能（モック不要、実際の RSS/API を叩く）
- `handler.py` はローカルから `python -c "from src.handler import handler; handler({}, {})"` で動作確認可能
- Lambda コンソールからテストイベント（空の JSON）で手動実行可能
