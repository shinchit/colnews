from fetchers import Article
from fetchers.base_rss import fetch_rss

FEED_URL = "https://zenn.dev/feed"


def fetch(max_items: int = 10) -> list[Article]:
    return fetch_rss(FEED_URL, "Zenn", max_items)
