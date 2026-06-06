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
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": (
                    "以下の技術ニュース記事を分析し、HTML形式で以下の3セクションを順番に出力してください。\n\n"
                    "## セクション1: 今日のトレンド\n"
                    "<h2>今日のトレンド</h2> タグを使い、本日の記事全体を俯瞰した傾向を2〜3文で説明してください。"
                    "どんなトピックが多いか、業界の関心がどこに向いているかを簡潔にまとめてください。\n\n"
                    "## セクション2: おすすめ記事\n"
                    "<h2>おすすめ記事</h2> タグを使い、特に注目すべき記事を3〜5件ピックアップしてください。\n"
                    "各記事は <li><a href=\"URL\">タイトル</a> - おすすめ理由（1行）</li> の形式にしてください。\n\n"
                    "## セクション3: カテゴリ別一覧\n"
                    "<h2>カテゴリ別一覧</h2> タグを使い、全記事をカテゴリ別（AI/ML、Web開発、インフラ、セキュリティ、その他）に整理し、"
                    "各記事を <li><a href=\"URL\">タイトル</a> - 要約（1行）</li> の形式にしてください。\n\n"
                    f"記事リスト:\n{article_lines}"
                ),
            }
        ],
    )
    return message.content[0].text
