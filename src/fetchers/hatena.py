from fetchers import Article
from fetchers.base_rss import fetch_rss

FEED_URL = "https://b.hatena.ne.jp/hotentry/it.rss"


def fetch(max_items: int = 10) -> list[Article]:
    return fetch_rss(FEED_URL, "はてなブックマーク", max_items)
