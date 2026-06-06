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
