import logging
import re
import os
from datetime import date

import boto3

import mailer
import summarizer
from fetchers import hackernews, hatena, keyword_news, qiita, reddit, x_twitter, youtube, zenn

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _inline_digest_styles(digest: str) -> str:
    """Claude 生成の HTML タグにインラインスタイルを付与する（メールクライアント互換）。"""
    h2_style = (
        "font-size:17px;font-weight:700;color:#1a1a2e;"
        "margin:28px 0 12px;padding:8px 14px;"
        "background-color:#f0f4ff;border-left:4px solid #0f3460;"
    )
    li_style = (
        "padding:10px 12px;margin-bottom:6px;"
        "background-color:#f9fafc;border:1px solid #e8ecf0;"
        "border-radius:6px;font-size:14px;line-height:1.6;list-style:none;"
    )
    a_style = "color:#0f3460;text-decoration:none;font-weight:500;"
    p_style = "margin:0 0 12px;color:#4a5568;font-size:15px;line-height:1.7;"
    ul_style = "margin:8px 0 16px;padding-left:0;"

    digest = re.sub(r"<h2([^>]*)>", f'<h2\\1 style="{h2_style}">', digest)
    digest = re.sub(r"<li([^>]*)>", f'<li\\1 style="{li_style}">', digest)
    digest = re.sub(r"<a([^>]*)>", f'<a\\1 style="{a_style}">', digest)
    digest = re.sub(r"<p([^>]*)>", f'<p\\1 style="{p_style}">', digest)
    digest = re.sub(r"<ul([^>]*)>", f'<ul\\1 style="{ul_style}">', digest)
    return digest


def _build_html_email(digest: str, today: str) -> str:
    styled_digest = _inline_digest_styles(digest)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f4f6f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;">
    <tr><td align="center" style="padding:24px 16px;">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <tr>
          <td style="background-color:#0f3460;padding:28px 32px 24px;text-align:center;">
            <p style="margin:0 0 4px;color:#a8c4e0;font-size:12px;letter-spacing:2px;text-transform:uppercase;">Tech News Digest</p>
            <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:600;">技術ニュースダイジェスト</h1>
            <p style="margin:8px 0 0;color:#7ec8e3;font-size:13px;">{today}</p>
          </td>
        </tr>

        <tr>
          <td style="padding:28px 32px;">
            {styled_digest}
          </td>
        </tr>

        <tr>
          <td style="background-color:#f0f4ff;padding:14px 32px;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0;color:#718096;font-size:12px;">colnews &mdash; Powered by Claude AI &amp; AWS Lambda</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


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
        body_html=_build_html_email(digest, today),
        from_addr=from_addr,
        to_addrs=to_addrs,
    )
    logger.info("Email sent successfully")
