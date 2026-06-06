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
