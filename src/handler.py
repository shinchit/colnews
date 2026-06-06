import logging
import os
from datetime import date

import boto3

import mailer
import summarizer
from fetchers import hackernews, hatena, keyword_news, qiita, reddit, x_twitter, youtube, zenn

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _get_secret(secret_arn: str) -> str:
    client = boto3.client("secretsmanager")
    return client.get_secret_value(SecretId=secret_arn)["SecretString"]


def main(event, context):
    max_items = int(os.environ.get("MAX_ITEMS_PER_SOURCE", "10"))
    model = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    from_addr = os.environ["SES_FROM_ADDRESS"]
    to_addrs = os.environ["TO_ADDRESSES"].split(",")
    reddit_subs = os.environ.get("REDDIT_SUBREDDITS", "programming,tech").split(",")
    yt_channels = [c for c in os.environ.get("YOUTUBE_CHANNEL_IDS", "").split(",") if c]
    keywords = os.environ.get("SEARCH_KEYWORDS", "AI,LLM,AWS,TypeScript,Claude,Gemini").split(",")

    anthropic_key = _get_secret(os.environ["ANTHROPIC_SECRET_ARN"])
    tavily_key = _get_secret(os.environ["TAVILY_SECRET_ARN"])

    fetchers = [
        ("Qiita", lambda: qiita.fetch(max_items)),
        ("Zenn", lambda: zenn.fetch(max_items)),
        ("はてなブックマーク", lambda: hatena.fetch(max_items)),
        ("Hacker News", lambda: hackernews.fetch(max_items)),
        ("Reddit", lambda: reddit.fetch(reddit_subs, max_items)),
        ("YouTube", lambda: youtube.fetch(yt_channels, max_items)),
        ("X/Twitter", lambda: x_twitter.fetch(tavily_key, keywords, max_items)),
        ("Keyword News", lambda: keyword_news.fetch(tavily_key, keywords, max_items)),
    ]

    all_articles = []
    for name, fn in fetchers:
        try:
            articles = fn()
            all_articles.extend(articles)
            logger.info("%s: %d articles", name, len(articles))
        except Exception as exc:
            logger.warning("%s failed: %s", name, exc)

    if not all_articles:
        logger.warning("No articles fetched, skipping email")
        return

    digest = summarizer.summarize(all_articles, model, anthropic_key)

    today = date.today().strftime("%Y年%m月%d日")
    mailer.send_email(
        subject=f"技術ニュースダイジェスト {today}",
        body_html=f"<html><body>{digest}</body></html>",
        from_addr=from_addr,
        to_addrs=to_addrs,
    )
    logger.info("Email sent successfully")
