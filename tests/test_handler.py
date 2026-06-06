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
