import anthropic

from fetchers import Article


def summarize(articles: list[Article], model: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    article_lines = "\n".join(
        f"[{a.source}] {a.title}\nURL: {a.url}\n{a.description}"
        for a in articles
    )

    message = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": (
                    "以下の技術ニュース記事をカテゴリ別（AI/ML、Web開発、インフラ、セキュリティ、その他）に整理し、"
                    "各記事を日本語1行で要約してください。\n"
                    "HTML形式で出力し、各カテゴリは<h2>タグ、各記事は"
                    "<li><a href=\"URL\">タイトル</a> - 要約</li> の形式にしてください。\n\n"
                    f"記事リスト:\n{article_lines}"
                ),
            }
        ],
    )
    return message.content[0].text
