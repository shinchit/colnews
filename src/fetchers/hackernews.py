import requests
from fetchers import Article

HN_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def fetch(max_items: int = 10) -> list[Article]:
    ids = requests.get(HN_TOP_STORIES, timeout=10).json()[:max_items]
    articles = []
    for item_id in ids:
        item = requests.get(HN_ITEM.format(item_id), timeout=10).json()
        title = item.get("title", "")
        if not title:
            continue
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        description = (item.get("text") or "")[:200]
        articles.append(Article(source="Hacker News", title=title, url=url, description=description))
    return articles
