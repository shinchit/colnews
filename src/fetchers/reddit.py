import requests
from fetchers import Article

REDDIT_URL = "https://www.reddit.com/r/{}.json"
HEADERS = {"User-Agent": "colnews/1.0 (news aggregator)"}


def fetch(subreddits: list[str], max_items: int = 10) -> list[Article]:
    if not subreddits:
        return []
    per_subreddit = max(1, max_items // len(subreddits))
    articles = []
    for subreddit in subreddits:
        resp = requests.get(REDDIT_URL.format(subreddit), headers=HEADERS, timeout=10)
        posts = resp.json()["data"]["children"][:per_subreddit]
        for post in posts:
            p = post["data"]
            articles.append(Article(
                source=f"Reddit r/{subreddit}",
                title=p["title"],
                url=f"https://reddit.com{p['permalink']}",
                description=(p.get("selftext") or "")[:200],
            ))
    return articles
