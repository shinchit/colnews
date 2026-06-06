from tavily import TavilyClient

from fetchers import Article


def fetch(api_key: str, keywords: list[str], max_items: int = 10) -> list[Article]:
    if not keywords:
        return []
    client = TavilyClient(api_key=api_key)
    per_keyword = max(1, max_items // len(keywords))
    articles = []
    for keyword in keywords:
        results = client.search(query=keyword, max_results=per_keyword)
        for r in results.get("results", []):
            title = r.get("title", "")
            url = r.get("url", "")
            if title and url:
                articles.append(Article(
                    source=f"News:{keyword}",
                    title=title,
                    url=url,
                    description=(r.get("content") or "")[:200],
                ))
    return articles
