from fetchers import Article
from fetchers.base_rss import fetch_rss

FEED_URL = "https://qiita.com/popular-items/feed.atom"


def fetch(max_items: int = 10) -> list[Article]:
    return fetch_rss(FEED_URL, "Qiita", max_items)
