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
