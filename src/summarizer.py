import logging

import anthropic

from fetchers import Article

logger = logging.getLogger(__name__)


def summarize(articles: list[Article], model: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    article_lines = "\n".join(
        f"[{a.source}] {a.title}\nURL: {a.url}\n{a.description}"
        for a in articles
    )

    message = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": (
                    "以下の技術ニュース記事を分析してください。\n"
                    "【重要】出力はHTMLタグのみを使用してください。マークダウン（#、##、**、- など）は絶対に使用しないでください。"
                    "```html などのコードブロックも使用しないでください。\n\n"
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
    if message.stop_reason == "max_tokens":
        logger.warning("summarize: output was truncated (stop_reason=max_tokens)")

    text = message.content[0].text

    # コードブロックを除去
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    # HTML タグが含まれていない場合（マークダウンで返ってきた場合）のフォールバック
    if "<h2>" not in text and "<li>" not in text:
        logger.warning("summarize: response does not contain HTML tags, converting plain text")
        lines = text.splitlines()
        html_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("## ") or line.startswith("# "):
                heading = line.lstrip("#").strip()
                html_lines.append(f"<h2>{heading}</h2>")
            elif line.startswith("- ") or line.startswith("* "):
                html_lines.append(f"<li>{line[2:]}</li>")
            else:
                html_lines.append(f"<p>{line}</p>")
        text = "\n".join(html_lines)

    return text
