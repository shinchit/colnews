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
