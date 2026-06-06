from tavily import TavilyClient

from fetchers import Article


def fetch(api_key: str, keywords: list[str], max_items: int = 10) -> list[Article]:
    client = TavilyClient(api_key=api_key)
    query = " OR ".join(keywords) + " site:twitter.com"
    results = client.search(query=query, max_results=max_items)
    articles = []
    for r in results.get("results", []):
        title = r.get("title", "")
        url = r.get("url", "")
        if title and url:
            articles.append(Article(
                source="X/Twitter",
                title=title,
                url=url,
                description=(r.get("content") or "")[:200],
            ))
    return articles
