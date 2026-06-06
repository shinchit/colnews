# AWS EventBridge ニュース配信システム 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** EventBridge でトリガーされる Lambda が 8 ソースから技術ニュースを収集し、Claude API (Haiku) でカテゴリ別日本語ダイジェストを生成して SES でメール配信する。

**Architecture:** Lambda モノリシック構成。各フェッチャーは独立して失敗可能。Claude API は 1 日 1 回のみ呼び出す。Tavily Search API で X/Twitter とキーワードニュースを取得。CDK で Lambda + EventBridge + IAM を定義。

**Tech Stack:** Python 3.12、pytest、AWS Lambda、EventBridge、SES、Secrets Manager、Anthropic API (claude-haiku-4-5-20251001)、Tavily Python SDK、feedparser、requests、AWS CDK v2 (Python)

---

## ファイル構成

```
colnews/
├── cdk/
│   ├── app.py
│   └── colnews_stack.py
├── src/
│   ├── handler.py
│   ├── summarizer.py
│   ├── mailer.py
│   └── fetchers/
│       ├── __init__.py          ← Article dataclass
│       ├── base_rss.py          ← RSS/Atom 共通パーサ
│       ├── qiita.py
│       ├── zenn.py
│       ├── hatena.py
│       ├── hackernews.py
│       ├── reddit.py
│       ├── youtube.py
│       ├── x_twitter.py
│       └── keyword_news.py
├── tests/
│   ├── test_base_rss.py
│   ├── test_hackernews.py
│   ├── test_reddit.py
│   ├── test_youtube.py
│   ├── test_tavily.py
│   ├── test_summarizer.py
│   ├── test_mailer.py
│   └── test_handler.py
├── src/requirements.txt
├── requirements.txt             ← CDK 依存
├── pyproject.toml               ← pytest 設定
├── cdk.json
└── .gitignore
```

---

### Task 1: プロジェクトスキャフォールド

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `src/requirements.txt`
- Create: `cdk.json`
- Create: `cdk/app.py`

- [ ] **Step 1: .gitignore を作成する**

```
__pycache__/
*.pyc
*.pyo
.venv/
venv/
cdk.out/
.pytest_cache/
*.egg-info/
.env
dist/
.DS_Store
```

- [ ] **Step 2: pyproject.toml を作成する**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 3: requirements.txt (CDK 用) を作成する**

```
aws-cdk-lib>=2.100.0
constructs>=10.0.0
aws-cdk.aws-lambda-python-alpha>=2.100.0a0
```

- [ ] **Step 4: src/requirements.txt (Lambda 用) を作成する**

```
anthropic>=0.40.0
requests>=2.31.0
feedparser>=6.0.11
tavily-python>=0.3.0
```

- [ ] **Step 5: cdk.json を作成する**

```json
{
  "app": "python cdk/app.py",
  "context": {
    "ses_from_address": "YOUR_FROM_ADDRESS@example.com",
    "to_addresses": "YOUR_TO_ADDRESS@example.com",
    "youtube_channel_ids": "",
    "reddit_subreddits": "programming,tech",
    "search_keywords": "AI,LLM,AWS,TypeScript,Claude,Gemini",
    "anthropic_secret_name": "colnews/anthropic-api-key",
    "tavily_secret_name": "colnews/tavily-api-key"
  }
}
```

- [ ] **Step 6: cdk/app.py を作成する**

```python
#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import aws_cdk as cdk
from colnews_stack import ColnewsStack

app = cdk.App()
ColnewsStack(app, "ColnewsStack")
app.synth()
```

- [ ] **Step 7: 仮想環境を作成して依存をインストールする**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
pip install -r src/requirements.txt
```

- [ ] **Step 8: コミットする**

```bash
git add .gitignore pyproject.toml requirements.txt src/requirements.txt cdk.json cdk/app.py
git commit -m "feat: add project scaffold"
```

---

### Task 2: Article dataclass

**Files:**
- Create: `src/fetchers/__init__.py`
- Create: `tests/test_base_rss.py` (最初のテスト)

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_base_rss.py`:
```python
from fetchers import Article


def test_article_dataclass():
    article = Article(
        source="Qiita",
        title="テスト記事",
        url="https://qiita.com/test",
        description="テスト説明",
    )
    assert article.source == "Qiita"
    assert article.title == "テスト記事"
    assert article.url == "https://qiita.com/test"
    assert article.description == "テスト説明"
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_base_rss.py::test_article_dataclass -v
```

期待結果: `ModuleNotFoundError: No module named 'fetchers'`

- [ ] **Step 3: Article dataclass を実装する**

`src/fetchers/__init__.py`:
```python
from dataclasses import dataclass


@dataclass
class Article:
    source: str
    title: str
    url: str
    description: str
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_base_rss.py::test_article_dataclass -v
```

期待結果: `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add src/fetchers/__init__.py tests/test_base_rss.py
git commit -m "feat: add Article dataclass"
```

---

### Task 3: RSS 共通パーサと Qiita/Zenn/はてブ フェッチャー

**Files:**
- Create: `src/fetchers/base_rss.py`
- Create: `src/fetchers/qiita.py`
- Create: `src/fetchers/zenn.py`
- Create: `src/fetchers/hatena.py`
- Modify: `tests/test_base_rss.py`

- [ ] **Step 1: base_rss のテストを書く**

`tests/test_base_rss.py` に追記:
```python
from unittest.mock import patch, MagicMock

from fetchers import Article
from fetchers.base_rss import fetch_rss


def test_article_dataclass():
    article = Article(
        source="Qiita",
        title="テスト記事",
        url="https://qiita.com/test",
        description="テスト説明",
    )
    assert article.source == "Qiita"
    assert article.title == "テスト記事"
    assert article.url == "https://qiita.com/test"
    assert article.description == "テスト説明"


def test_fetch_rss_returns_articles():
    mock_entry = {
        "title": "Test Article",
        "link": "https://example.com/article",
        "summary": "A test description",
    }
    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch("fetchers.base_rss.feedparser.parse", return_value=mock_feed):
        articles = fetch_rss("https://example.com/feed", "TestSource", 5)

    assert len(articles) == 1
    assert articles[0].title == "Test Article"
    assert articles[0].url == "https://example.com/article"
    assert articles[0].source == "TestSource"
    assert articles[0].description == "A test description"


def test_fetch_rss_respects_max_items():
    mock_feed = MagicMock()
    mock_feed.entries = [
        {"title": f"Article {i}", "link": f"https://example.com/{i}", "summary": ""}
        for i in range(20)
    ]

    with patch("fetchers.base_rss.feedparser.parse", return_value=mock_feed):
        articles = fetch_rss("https://example.com/feed", "TestSource", 5)

    assert len(articles) == 5


def test_fetch_rss_skips_entries_without_title_or_link():
    mock_feed = MagicMock()
    mock_feed.entries = [
        {"title": "", "link": "https://example.com/1", "summary": ""},
        {"title": "Valid", "link": "", "summary": ""},
        {"title": "Valid", "link": "https://example.com/2", "summary": ""},
    ]

    with patch("fetchers.base_rss.feedparser.parse", return_value=mock_feed):
        articles = fetch_rss("https://example.com/feed", "TestSource", 10)

    assert len(articles) == 1
    assert articles[0].title == "Valid"


def test_fetch_rss_truncates_description():
    long_description = "x" * 300
    mock_feed = MagicMock()
    mock_feed.entries = [
        {"title": "Title", "link": "https://example.com/1", "summary": long_description}
    ]

    with patch("fetchers.base_rss.feedparser.parse", return_value=mock_feed):
        articles = fetch_rss("https://example.com/feed", "TestSource", 10)

    assert len(articles[0].description) == 200
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_base_rss.py -v
```

期待結果: `test_article_dataclass PASSED`, 残りは `ImportError` で失敗

- [ ] **Step 3: base_rss.py を実装する**

`src/fetchers/base_rss.py`:
```python
import feedparser
from fetchers import Article


def fetch_rss(feed_url: str, source_name: str, max_items: int) -> list[Article]:
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:max_items]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        description = (entry.get("summary") or entry.get("description") or "")[:200]
        if title and link:
            articles.append(Article(source=source_name, title=title, url=link, description=description))
    return articles
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_base_rss.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 5: Qiita/Zenn/はてブ フェッチャーを実装する（テスト不要 — base_rss でカバー済み）**

`src/fetchers/qiita.py`:
```python
from fetchers import Article
from fetchers.base_rss import fetch_rss

FEED_URL = "https://qiita.com/popular-items/feed.atom"


def fetch(max_items: int = 10) -> list[Article]:
    return fetch_rss(FEED_URL, "Qiita", max_items)
```

`src/fetchers/zenn.py`:
```python
from fetchers import Article
from fetchers.base_rss import fetch_rss

FEED_URL = "https://zenn.dev/feed"


def fetch(max_items: int = 10) -> list[Article]:
    return fetch_rss(FEED_URL, "Zenn", max_items)
```

`src/fetchers/hatena.py`:
```python
from fetchers import Article
from fetchers.base_rss import fetch_rss

FEED_URL = "https://b.hatena.ne.jp/hotentry/it.rss"


def fetch(max_items: int = 10) -> list[Article]:
    return fetch_rss(FEED_URL, "はてなブックマーク", max_items)
```

- [ ] **Step 6: コミットする**

```bash
git add src/fetchers/base_rss.py src/fetchers/qiita.py src/fetchers/zenn.py src/fetchers/hatena.py tests/test_base_rss.py
git commit -m "feat: add RSS fetchers (base, Qiita, Zenn, Hatena)"
```

---

### Task 4: Hacker News フェッチャー

**Files:**
- Create: `src/fetchers/hackernews.py`
- Create: `tests/test_hackernews.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_hackernews.py`:
```python
from unittest.mock import patch, MagicMock, call

from fetchers.hackernews import fetch


def test_hackernews_fetch_returns_articles():
    mock_ids_resp = MagicMock()
    mock_ids_resp.json.return_value = [111, 222]

    mock_item_resp = MagicMock()
    mock_item_resp.json.return_value = {
        "title": "HN Article",
        "url": "https://example.com/hn",
        "text": "",
    }

    with patch("fetchers.hackernews.requests.get") as mock_get:
        mock_get.side_effect = [mock_ids_resp, mock_item_resp, mock_item_resp]
        articles = fetch(max_items=2)

    assert len(articles) == 2
    assert articles[0].source == "Hacker News"
    assert articles[0].title == "HN Article"
    assert articles[0].url == "https://example.com/hn"


def test_hackernews_fetch_uses_hn_url_when_no_url():
    mock_ids_resp = MagicMock()
    mock_ids_resp.json.return_value = [999]

    mock_item_resp = MagicMock()
    mock_item_resp.json.return_value = {
        "id": 999,
        "title": "Ask HN: Something",
    }

    with patch("fetchers.hackernews.requests.get") as mock_get:
        mock_get.side_effect = [mock_ids_resp, mock_item_resp]
        articles = fetch(max_items=1)

    assert len(articles) == 1
    assert "news.ycombinator.com/item?id=999" in articles[0].url


def test_hackernews_fetch_skips_items_without_title():
    mock_ids_resp = MagicMock()
    mock_ids_resp.json.return_value = [1]

    mock_item_resp = MagicMock()
    mock_item_resp.json.return_value = {"id": 1}

    with patch("fetchers.hackernews.requests.get") as mock_get:
        mock_get.side_effect = [mock_ids_resp, mock_item_resp]
        articles = fetch(max_items=1)

    assert len(articles) == 0
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_hackernews.py -v
```

期待結果: `ModuleNotFoundError: No module named 'fetchers.hackernews'`

- [ ] **Step 3: hackernews.py を実装する**

`src/fetchers/hackernews.py`:
```python
import requests
from fetchers import Article

HN_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch(max_items: int = 10) -> list[Article]:
    ids = requests.get(HN_TOP_STORIES, timeout=10).json()[:max_items]
    articles = []
    for item_id in ids:
        item = requests.get(HN_ITEM.format(item_id), timeout=10).json()
        title = item.get("title", "")
        if not title:
            continue
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        description = (item.get("text") or "")[:200]
        articles.append(Article(source="Hacker News", title=title, url=url, description=description))
    return articles
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_hackernews.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add src/fetchers/hackernews.py tests/test_hackernews.py
git commit -m "feat: add Hacker News fetcher"
```

---

### Task 5: Reddit フェッチャー

**Files:**
- Create: `src/fetchers/reddit.py`
- Create: `tests/test_reddit.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_reddit.py`:
```python
from unittest.mock import patch, MagicMock

from fetchers.reddit import fetch


def test_reddit_fetch_returns_articles():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Reddit Post Title",
                        "permalink": "/r/programming/comments/abc/post/",
                        "selftext": "Post body text",
                    }
                }
            ]
        }
    }

    with patch("fetchers.reddit.requests.get", return_value=mock_resp):
        articles = fetch(["programming"], max_items=5)

    assert len(articles) == 1
    assert articles[0].source == "Reddit r/programming"
    assert articles[0].title == "Reddit Post Title"
    assert "reddit.com/r/programming" in articles[0].url


def test_reddit_fetch_multiple_subreddits():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Post",
                        "permalink": "/r/tech/comments/xyz/",
                        "selftext": "",
                    }
                }
            ]
        }
    }

    with patch("fetchers.reddit.requests.get", return_value=mock_resp):
        articles = fetch(["programming", "tech"], max_items=4)

    assert len(articles) == 2


def test_reddit_fetch_empty_subreddits_returns_empty():
    articles = fetch([], max_items=5)
    assert articles == []
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_reddit.py -v
```

期待結果: `ModuleNotFoundError: No module named 'fetchers.reddit'`

- [ ] **Step 3: reddit.py を実装する**

`src/fetchers/reddit.py`:
```python
import requests
from fetchers import Article

REDDIT_URL = "https://www.reddit.com/r/{}.json"
HEADERS = {"User-Agent": "colnews/1.0 (news aggregator)"}


def fetch(subreddits: list[str], max_items: int = 10) -> list[Article]:
    if not subreddits:
        return []
    per_subreddit = max(1, max_items // len(subreddits))
    articles = []
    for subreddit in subreddits:
        resp = requests.get(REDDIT_URL.format(subreddit), headers=HEADERS, timeout=10)
        posts = resp.json()["data"]["children"][:per_subreddit]
        for post in posts:
            p = post["data"]
            articles.append(Article(
                source=f"Reddit r/{subreddit}",
                title=p["title"],
                url=f"https://reddit.com{p['permalink']}",
                description=(p.get("selftext") or "")[:200],
            ))
    return articles
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_reddit.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add src/fetchers/reddit.py tests/test_reddit.py
git commit -m "feat: add Reddit fetcher"
```

---

### Task 6: YouTube フェッチャー

**Files:**
- Create: `src/fetchers/youtube.py`
- Create: `tests/test_youtube.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_youtube.py`:
```python
from unittest.mock import patch, MagicMock

from fetchers.youtube import fetch

YOUTUBE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <entry>
    <title>Test Video Title</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
    <media:group>
      <media:description>This is a test video description.</media:description>
    </media:group>
  </entry>
</feed>"""


def test_youtube_fetch_returns_articles():
    mock_resp = MagicMock()
    mock_resp.text = YOUTUBE_XML

    with patch("fetchers.youtube.requests.get", return_value=mock_resp):
        articles = fetch(["CHANNEL123"], max_items=5)

    assert len(articles) == 1
    assert articles[0].title == "Test Video Title"
    assert articles[0].url == "https://www.youtube.com/watch?v=abc123"
    assert articles[0].source == "YouTube"
    assert "test video description" in articles[0].description


def test_youtube_fetch_empty_channels_returns_empty():
    articles = fetch([], max_items=5)
    assert articles == []


def test_youtube_fetch_multiple_channels():
    mock_resp = MagicMock()
    mock_resp.text = YOUTUBE_XML

    with patch("fetchers.youtube.requests.get", return_value=mock_resp):
        articles = fetch(["CH1", "CH2"], max_items=4)

    assert len(articles) == 2
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_youtube.py -v
```

期待結果: `ModuleNotFoundError: No module named 'fetchers.youtube'`

- [ ] **Step 3: youtube.py を実装する**

`src/fetchers/youtube.py`:
```python
import xml.etree.ElementTree as ET

import requests

from fetchers import Article

YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
}


def fetch(channel_ids: list[str], max_items: int = 10) -> list[Article]:
    if not channel_ids:
        return []
    per_channel = max(1, max_items // len(channel_ids))
    articles = []
    for channel_id in channel_ids:
        resp = requests.get(YOUTUBE_RSS.format(channel_id), timeout=10)
        root = ET.fromstring(resp.text)
        entries = root.findall("atom:entry", NS)[:per_channel]
        for entry in entries:
            title = entry.findtext("atom:title", namespaces=NS) or ""
            link_el = entry.find("atom:link", NS)
            url = link_el.get("href", "") if link_el is not None else ""
            desc_el = entry.find("media:group/media:description", NS)
            description = ((desc_el.text or "") if desc_el is not None else "")[:200]
            if title and url:
                articles.append(Article(source="YouTube", title=title, url=url, description=description))
    return articles
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_youtube.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add src/fetchers/youtube.py tests/test_youtube.py
git commit -m "feat: add YouTube fetcher"
```

---

### Task 7: Tavily フェッチャー（X/Twitter + キーワードニュース）

**Files:**
- Create: `src/fetchers/x_twitter.py`
- Create: `src/fetchers/keyword_news.py`
- Create: `tests/test_tavily.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_tavily.py`:
```python
from unittest.mock import patch, MagicMock

from fetchers.x_twitter import fetch as fetch_twitter
from fetchers.keyword_news import fetch as fetch_keyword_news


def test_x_twitter_fetch_returns_articles():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {
                "title": "Tweet about AI",
                "url": "https://twitter.com/user/status/123",
                "content": "Some tweet content about AI",
            }
        ]
    }

    with patch("fetchers.x_twitter.TavilyClient", return_value=mock_client):
        articles = fetch_twitter("fake-api-key", ["AI", "LLM"], max_items=5)

    assert len(articles) == 1
    assert articles[0].source == "X/Twitter"
    assert articles[0].title == "Tweet about AI"
    assert articles[0].url == "https://twitter.com/user/status/123"

    call_kwargs = mock_client.search.call_args
    query_used = call_kwargs.kwargs.get("query") or call_kwargs.args[0]
    assert "site:twitter.com" in query_used


def test_x_twitter_fetch_empty_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}

    with patch("fetchers.x_twitter.TavilyClient", return_value=mock_client):
        articles = fetch_twitter("fake-api-key", ["AI"], max_items=5)

    assert articles == []


def test_keyword_news_fetch_returns_articles():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {
                "title": "AI News Article",
                "url": "https://news.example.com/ai",
                "content": "News about artificial intelligence",
            }
        ]
    }

    with patch("fetchers.keyword_news.TavilyClient", return_value=mock_client):
        articles = fetch_keyword_news("fake-api-key", ["AI", "LLM"], max_items=4)

    assert len(articles) == 2
    assert all(a.source.startswith("News:") for a in articles)
    assert mock_client.search.call_count == 2


def test_keyword_news_empty_keywords_returns_empty():
    articles = fetch_keyword_news("fake-api-key", [], max_items=5)
    assert articles == []
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_tavily.py -v
```

期待結果: `ModuleNotFoundError: No module named 'fetchers.x_twitter'`

- [ ] **Step 3: x_twitter.py を実装する**

`src/fetchers/x_twitter.py`:
```python
from tavily import TavilyClient

from fetchers import Article


def fetch(api_key: str, keywords: list[str], max_items: int = 10) -> list[Article]:
    client = TavilyClient(api_key=api_key)
    query = " OR ".join(keywords) + " site:twitter.com"
    results = client.search(query=query, max_results=max_items)
    articles = []
    for r in results.get("results", []):
        title = r.get("title", "")
        url = r.get("url", "")
        if title and url:
            articles.append(Article(
                source="X/Twitter",
                title=title,
                url=url,
                description=(r.get("content") or "")[:200],
            ))
    return articles
```

- [ ] **Step 4: keyword_news.py を実装する**

`src/fetchers/keyword_news.py`:
```python
from tavily import TavilyClient

from fetchers import Article


def fetch(api_key: str, keywords: list[str], max_items: int = 10) -> list[Article]:
    if not keywords:
        return []
    client = TavilyClient(api_key=api_key)
    per_keyword = max(1, max_items // len(keywords))
    articles = []
    for keyword in keywords:
        results = client.search(query=keyword, max_results=per_keyword)
        for r in results.get("results", []):
            title = r.get("title", "")
            url = r.get("url", "")
            if title and url:
                articles.append(Article(
                    source=f"News:{keyword}",
                    title=title,
                    url=url,
                    description=(r.get("content") or "")[:200],
                ))
    return articles
```

- [ ] **Step 5: テストを実行してパスを確認する**

```bash
pytest tests/test_tavily.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 6: コミットする**

```bash
git add src/fetchers/x_twitter.py src/fetchers/keyword_news.py tests/test_tavily.py
git commit -m "feat: add Tavily fetchers for X/Twitter and keyword news"
```

---

### Task 8: Summarizer（Claude API）

**Files:**
- Create: `src/summarizer.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_summarizer.py`:
```python
from unittest.mock import patch, MagicMock

from fetchers import Article
from summarizer import summarize


def test_summarize_returns_html():
    mock_content = MagicMock()
    mock_content.text = "<h2>AI/ML</h2><ul><li><a href='https://example.com'>Test</a> - 説明</li></ul>"

    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    articles = [
        Article(source="Qiita", title="Test Article", url="https://example.com", description="Test desc")
    ]

    with patch("summarizer.anthropic.Anthropic", return_value=mock_client):
        result = summarize(articles, "claude-haiku-4-5-20251001", "fake-api-key")

    assert "<h2>" in result
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
    assert call_kwargs["max_tokens"] == 2000


def test_summarize_includes_all_articles_in_prompt():
    mock_content = MagicMock()
    mock_content.text = "<h2>その他</h2><ul><li>Result</li></ul>"

    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    articles = [
        Article(source="Qiita", title="Article One", url="https://qiita.com/1", description="Desc 1"),
        Article(source="Zenn", title="Article Two", url="https://zenn.dev/2", description="Desc 2"),
    ]

    with patch("summarizer.anthropic.Anthropic", return_value=mock_client):
        summarize(articles, "claude-haiku-4-5-20251001", "fake-api-key")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    prompt_text = call_kwargs["messages"][0]["content"]
    assert "Article One" in prompt_text
    assert "Article Two" in prompt_text
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_summarizer.py -v
```

期待結果: `ModuleNotFoundError: No module named 'summarizer'`

- [ ] **Step 3: summarizer.py を実装する**

`src/summarizer.py`:
```python
import anthropic

from fetchers import Article


def summarize(articles: list[Article], model: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    article_lines = "\n".join(
        f"[{a.source}] {a.title}\nURL: {a.url}\n{a.description}"
        for a in articles
    )

    message = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": (
                    "以下の技術ニュース記事をカテゴリ別（AI/ML、Web開発、インフラ、セキュリティ、その他）に整理し、"
                    "各記事を日本語1行で要約してください。\n"
                    "HTML形式で出力し、各カテゴリは<h2>タグ、各記事は"
                    "<li><a href=\"URL\">タイトル</a> - 要約</li> の形式にしてください。\n\n"
                    f"記事リスト:\n{article_lines}"
                ),
            }
        ],
    )
    return message.content[0].text
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_summarizer.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add src/summarizer.py tests/test_summarizer.py
git commit -m "feat: add summarizer using Claude API"
```

---

### Task 9: Mailer（SES）

**Files:**
- Create: `src/mailer.py`
- Create: `tests/test_mailer.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_mailer.py`:
```python
from unittest.mock import patch, MagicMock

from mailer import send_email


def test_send_email_calls_ses():
    with patch("mailer.boto3.client") as mock_boto3:
        mock_ses = MagicMock()
        mock_boto3.return_value = mock_ses

        send_email(
            subject="Test Subject",
            body_html="<html><body>test</body></html>",
            from_addr="from@example.com",
            to_addrs=["to@example.com"],
        )

    mock_boto3.assert_called_once_with("ses")
    mock_ses.send_email.assert_called_once()

    kwargs = mock_ses.send_email.call_args.kwargs
    assert kwargs["Source"] == "from@example.com"
    assert kwargs["Destination"]["ToAddresses"] == ["to@example.com"]
    assert kwargs["Message"]["Subject"]["Data"] == "Test Subject"
    assert "<html>" in kwargs["Message"]["Body"]["Html"]["Data"]


def test_send_email_multiple_recipients():
    with patch("mailer.boto3.client") as mock_boto3:
        mock_ses = MagicMock()
        mock_boto3.return_value = mock_ses

        send_email(
            subject="Test",
            body_html="<p>body</p>",
            from_addr="from@example.com",
            to_addrs=["a@example.com", "b@example.com"],
        )

    kwargs = mock_ses.send_email.call_args.kwargs
    assert len(kwargs["Destination"]["ToAddresses"]) == 2
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_mailer.py -v
```

期待結果: `ModuleNotFoundError: No module named 'mailer'`

- [ ] **Step 3: mailer.py を実装する**

`src/mailer.py`:
```python
import boto3


def send_email(subject: str, body_html: str, from_addr: str, to_addrs: list[str]) -> None:
    ses = boto3.client("ses")
    ses.send_email(
        Source=from_addr,
        Destination={"ToAddresses": to_addrs},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Html": {"Data": body_html, "Charset": "UTF-8"}},
        },
    )
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_mailer.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 5: コミットする**

```bash
git add src/mailer.py tests/test_mailer.py
git commit -m "feat: add SES mailer"
```

---

### Task 10: Lambda ハンドラ（オーケストレーター）

**Files:**
- Create: `src/handler.py`
- Create: `tests/test_handler.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_handler.py`:
```python
import os
from unittest.mock import patch, MagicMock

import pytest

from fetchers import Article
from handler import main


DUMMY_ARTICLES = [
    Article(source="Qiita", title="Test Title", url="https://example.com", description="Test")
]

ENV = {
    "SES_FROM_ADDRESS": "from@example.com",
    "TO_ADDRESSES": "to@example.com",
    "ANTHROPIC_SECRET_ARN": "arn:aws:secretsmanager:ap-northeast-1:123:secret:anthropic",
    "TAVILY_SECRET_ARN": "arn:aws:secretsmanager:ap-northeast-1:123:secret:tavily",
    "MAX_ITEMS_PER_SOURCE": "5",
    "CLAUDE_MODEL": "claude-haiku-4-5-20251001",
    "REDDIT_SUBREDDITS": "programming",
    "YOUTUBE_CHANNEL_IDS": "",
    "SEARCH_KEYWORDS": "AI,LLM",
}


def test_main_fetches_and_sends_email(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)

    with (
        patch("handler._get_secret", return_value="fake-key"),
        patch("handler.qiita.fetch", return_value=DUMMY_ARTICLES),
        patch("handler.zenn.fetch", return_value=[]),
        patch("handler.hatena.fetch", return_value=[]),
        patch("handler.hackernews.fetch", return_value=[]),
        patch("handler.reddit.fetch", return_value=[]),
        patch("handler.youtube.fetch", return_value=[]),
        patch("handler.x_twitter.fetch", return_value=[]),
        patch("handler.keyword_news.fetch", return_value=[]),
        patch("handler.summarizer.summarize", return_value="<h2>AI/ML</h2>") as mock_summarize,
        patch("handler.mailer.send_email") as mock_send,
    ):
        main({}, {})

    mock_summarize.assert_called_once()
    mock_send.assert_called_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["from_addr"] == "from@example.com"
    assert kwargs["to_addrs"] == ["to@example.com"]
    assert "<h2>AI/ML</h2>" in kwargs["body_html"]


def test_main_skips_email_when_no_articles(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)

    with (
        patch("handler._get_secret", return_value="fake-key"),
        patch("handler.qiita.fetch", return_value=[]),
        patch("handler.zenn.fetch", return_value=[]),
        patch("handler.hatena.fetch", return_value=[]),
        patch("handler.hackernews.fetch", return_value=[]),
        patch("handler.reddit.fetch", return_value=[]),
        patch("handler.youtube.fetch", return_value=[]),
        patch("handler.x_twitter.fetch", return_value=[]),
        patch("handler.keyword_news.fetch", return_value=[]),
        patch("handler.mailer.send_email") as mock_send,
    ):
        main({}, {})

    mock_send.assert_not_called()


def test_main_continues_when_fetcher_fails(monkeypatch):
    for k, v in ENV.items():
        monkeypatch.setenv(k, v)

    with (
        patch("handler._get_secret", return_value="fake-key"),
        patch("handler.qiita.fetch", side_effect=Exception("Network error")),
        patch("handler.zenn.fetch", return_value=DUMMY_ARTICLES),
        patch("handler.hatena.fetch", return_value=[]),
        patch("handler.hackernews.fetch", return_value=[]),
        patch("handler.reddit.fetch", return_value=[]),
        patch("handler.youtube.fetch", return_value=[]),
        patch("handler.x_twitter.fetch", return_value=[]),
        patch("handler.keyword_news.fetch", return_value=[]),
        patch("handler.summarizer.summarize", return_value="<h2>Result</h2>"),
        patch("handler.mailer.send_email") as mock_send,
    ):
        main({}, {})

    mock_send.assert_called_once()
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
pytest tests/test_handler.py -v
```

期待結果: `ModuleNotFoundError: No module named 'handler'`

- [ ] **Step 3: handler.py を実装する**

`src/handler.py`:
```python
import logging
import os
from datetime import date

import boto3

import mailer
import summarizer
from fetchers import hackernews, hatena, keyword_news, qiita, reddit, x_twitter, youtube, zenn

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _get_secret(secret_arn: str) -> str:
    client = boto3.client("secretsmanager")
    return client.get_secret_value(SecretId=secret_arn)["SecretString"]


def main(event, context):
    max_items = int(os.environ.get("MAX_ITEMS_PER_SOURCE", "10"))
    model = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    from_addr = os.environ["SES_FROM_ADDRESS"]
    to_addrs = os.environ["TO_ADDRESSES"].split(",")
    reddit_subs = os.environ.get("REDDIT_SUBREDDITS", "programming,tech").split(",")
    yt_channels = [c for c in os.environ.get("YOUTUBE_CHANNEL_IDS", "").split(",") if c]
    keywords = os.environ.get("SEARCH_KEYWORDS", "AI,LLM,AWS,TypeScript,Claude,Gemini").split(",")

    anthropic_key = _get_secret(os.environ["ANTHROPIC_SECRET_ARN"])
    tavily_key = _get_secret(os.environ["TAVILY_SECRET_ARN"])

    fetchers = [
        ("Qiita", lambda: qiita.fetch(max_items)),
        ("Zenn", lambda: zenn.fetch(max_items)),
        ("はてなブックマーク", lambda: hatena.fetch(max_items)),
        ("Hacker News", lambda: hackernews.fetch(max_items)),
        ("Reddit", lambda: reddit.fetch(reddit_subs, max_items)),
        ("YouTube", lambda: youtube.fetch(yt_channels, max_items)),
        ("X/Twitter", lambda: x_twitter.fetch(tavily_key, keywords, max_items)),
        ("Keyword News", lambda: keyword_news.fetch(tavily_key, keywords, max_items)),
    ]

    all_articles = []
    for name, fn in fetchers:
        try:
            articles = fn()
            all_articles.extend(articles)
            logger.info("%s: %d articles", name, len(articles))
        except Exception as exc:
            logger.warning("%s failed: %s", name, exc)

    if not all_articles:
        logger.warning("No articles fetched, skipping email")
        return

    digest = summarizer.summarize(all_articles, model, anthropic_key)

    today = date.today().strftime("%Y年%m月%d日")
    mailer.send_email(
        subject=f"技術ニュースダイジェスト {today}",
        body_html=f"<html><body>{digest}</body></html>",
        from_addr=from_addr,
        to_addrs=to_addrs,
    )
    logger.info("Email sent successfully")
```

- [ ] **Step 4: テストを実行してパスを確認する**

```bash
pytest tests/test_handler.py -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 5: 全テストをまとめて実行する**

```bash
pytest tests/ -v
```

期待結果: 全テスト `PASSED`

- [ ] **Step 6: コミットする**

```bash
git add src/handler.py tests/test_handler.py
git commit -m "feat: add Lambda handler orchestrator"
```

---

### Task 11: CDK スタック

**Files:**
- Create: `cdk/colnews_stack.py`

> **前提:** `cdk bootstrap` 済み、Docker が起動中であること（`aws_lambda_python_alpha` がビルド時に使用する）。

- [ ] **Step 1: colnews_stack.py を実装する**

`cdk/colnews_stack.py`:
```python
import os

import aws_cdk as cdk
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_secretsmanager as secretsmanager
from aws_cdk import aws_lambda_python_alpha as python_lambda
from constructs import Construct


class ColnewsStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ctx = self.node
        anthropic_secret_name = ctx.try_get_context("anthropic_secret_name") or "colnews/anthropic-api-key"
        tavily_secret_name = ctx.try_get_context("tavily_secret_name") or "colnews/tavily-api-key"
        ses_from = ctx.try_get_context("ses_from_address") or ""
        to_addresses = ctx.try_get_context("to_addresses") or ""
        yt_channels = ctx.try_get_context("youtube_channel_ids") or ""
        reddit_subs = ctx.try_get_context("reddit_subreddits") or "programming,tech"
        keywords = ctx.try_get_context("search_keywords") or "AI,LLM,AWS,TypeScript,Claude,Gemini"

        anthropic_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "AnthropicSecret", anthropic_secret_name
        )
        tavily_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "TavilySecret", tavily_secret_name
        )

        entry_path = os.path.join(os.path.dirname(__file__), "..", "src")

        news_fn = python_lambda.PythonFunction(
            self,
            "ColnewsFunction",
            entry=entry_path,
            runtime=lambda_.Runtime.PYTHON_3_12,
            index="handler.py",
            handler="main",
            timeout=cdk.Duration.minutes(5),
            memory_size=512,
            environment={
                "ANTHROPIC_SECRET_ARN": anthropic_secret.secret_arn,
                "TAVILY_SECRET_ARN": tavily_secret.secret_arn,
                "SES_FROM_ADDRESS": ses_from,
                "TO_ADDRESSES": to_addresses,
                "MAX_ITEMS_PER_SOURCE": "10",
                "CLAUDE_MODEL": "claude-haiku-4-5-20251001",
                "YOUTUBE_CHANNEL_IDS": yt_channels,
                "REDDIT_SUBREDDITS": reddit_subs,
                "SEARCH_KEYWORDS": keywords,
            },
        )

        anthropic_secret.grant_read(news_fn)
        tavily_secret.grant_read(news_fn)

        news_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"],
            )
        )

        rule = events.Rule(
            self,
            "ColnewsSchedule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="21",
                day="*",
                month="*",
                year="*",
            ),
        )
        rule.add_target(targets.LambdaFunction(news_fn))
```

- [ ] **Step 2: cdk.json の ses_from_address と to_addresses を実際のアドレスに更新する**

`cdk.json` の以下の値を実際のアドレスに更新:
```json
"ses_from_address": "your-verified@example.com",
"to_addresses": "recipient@example.com"
```

- [ ] **Step 3: CDK synth でスタック定義を確認する**

```bash
cdk synth
```

期待結果: `cdk.out/` に CloudFormation テンプレートが生成される。エラーなし。

出力例:
```
Resources:
  ColnewsFunction...
  ColnewsSchedule...
```

- [ ] **Step 4: AWS Secrets Manager に API キーを登録する（未作成の場合）**

```bash
aws secretsmanager create-secret \
  --name colnews/anthropic-api-key \
  --secret-string "YOUR_ANTHROPIC_API_KEY"

aws secretsmanager create-secret \
  --name colnews/tavily-api-key \
  --secret-string "YOUR_TAVILY_API_KEY"
```

- [ ] **Step 5: デプロイする**

```bash
cdk deploy
```

期待結果:
```
ColnewsStack: deploying...
ColnewsStack: deployed successfully
```

- [ ] **Step 6: Lambda コンソールからテスト実行して動作確認する**

AWS コンソール → Lambda → `ColnewsStack-ColnewsFunction...` → テスト → 空の JSON `{}` を送信

CloudWatch Logs で各ソースの取得件数とメール送信成功ログを確認:
```
Qiita: 10 articles
Zenn: 10 articles
...
Email sent successfully
```

- [ ] **Step 7: コミットする**

```bash
git add cdk/colnews_stack.py
git commit -m "feat: add CDK stack with Lambda, EventBridge, and IAM"
```

- [ ] **Step 8: プッシュする**

```bash
git push
```
