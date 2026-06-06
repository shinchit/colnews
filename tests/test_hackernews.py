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
