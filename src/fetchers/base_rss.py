import feedparser
from fetchers import Article


def fetch_rss(feed_url: str, source_name: str, max_items: int) -> list[Article]:
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:max_items]:
        title = entry.get("title", "")
        link = entry.get("link", "")
        description = (entry.get("summary") or entry.get("description") or "")[:200]
        if title and link:
            articles.append(Article(source=source_name, title=title, url=link, description=description))
    return articles
