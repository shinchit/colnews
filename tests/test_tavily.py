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
