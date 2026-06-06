# colnews

Daily tech news digest delivered to your inbox, powered by AWS EventBridge + Lambda + Claude AI.

Every morning at 6:00 JST, colnews fetches articles from 8 sources, summarizes them with Claude (Haiku), and sends a styled HTML email via Amazon SES. The AI-generated summary is written in Japanese.

## Architecture

```
EventBridge Rule (cron: daily 21:00 UTC = 06:00 JST)
    │
    ▼
Lambda Function (Python 3.12, ARM64, 5 min timeout)
    │
    ├─ Qiita             RSS/Atom
    ├─ Zenn              RSS
    ├─ はてなブックマーク   RSS
    ├─ Hacker News       JSON API
    ├─ Reddit            JSON API
    ├─ YouTube           XML RSS
    ├─ X/Twitter         Tavily Search API
    └─ Keyword News      Tavily Search API
    │
    ├─ Claude API (Haiku) ── 1 call/day ──► HTML digest
    │    • Today's trends
    │    • Recommended articles
    │    • Category breakdown (AI/ML, Web, Infra, Security, Other)
    │
    └─ Amazon SES ──► Styled HTML email
```

Infrastructure is managed with **AWS CDK v2**.  
API keys are stored in **AWS Secrets Manager** — never in environment variables or code.

## Prerequisites

| Requirement | Notes |
|---|---|
| AWS account | SES sandbox lifted, or sender/recipient addresses verified |
| AWS CDK v2 | `npm install -g aws-cdk` |
| Docker Desktop | Required for CDK's Python Lambda bundling (ARM64) |
| Python 3.12 | For CDK app and local development |
| Anthropic API key | [console.anthropic.com](https://console.anthropic.com) |
| Tavily API key | [app.tavily.com](https://app.tavily.com) — free tier covers ~210 req/month |

## Setup

### 1. Clone and install CDK dependencies

```bash
git clone https://github.com/YOUR_USERNAME/colnews.git
cd colnews
pip install -r requirements.txt
```

### 2. Bootstrap CDK (first time only)

```bash
cdk bootstrap
```

### 3. Store API keys in Secrets Manager

```bash
aws secretsmanager create-secret \
  --name colnews/anthropic-api-key \
  --secret-string "sk-ant-..."

aws secretsmanager create-secret \
  --name colnews/tavily-api-key \
  --secret-string "tvly-..."
```

### 4. Configure `cdk.json`

Edit the `context` block in `cdk.json`:

```json
{
  "app": "python3 cdk/app.py",
  "context": {
    "ses_from_address": "noreply@yourdomain.com",
    "to_addresses": "you@example.com",
    "youtube_channel_ids": "",
    "reddit_subreddits": "programming,tech",
    "search_keywords": "AI,LLM,AWS,TypeScript,Claude,Gemini",
    "anthropic_secret_name": "colnews/anthropic-api-key",
    "tavily_secret_name": "colnews/tavily-api-key"
  }
}
```

| Key | Description |
|---|---|
| `ses_from_address` | Verified SES sender address |
| `to_addresses` | Comma-separated recipient list |
| `youtube_channel_ids` | Comma-separated YouTube channel IDs (leave empty to skip) |
| `reddit_subreddits` | Comma-separated subreddit names |
| `search_keywords` | Keywords for X/Twitter and keyword-news searches |
| `anthropic_secret_name` | Secrets Manager secret name for Anthropic API key |
| `tavily_secret_name` | Secrets Manager secret name for Tavily API key |

### 5. Deploy

```bash
# Docker Desktop must be running
cdk deploy
```

### 6. Test immediately

Invoke the Lambda manually from the AWS console (use an empty JSON `{}` as test event), or:

```bash
aws lambda invoke \
  --function-name ColnewsStack-ColnewsFunction \
  --payload '{}' \
  response.json && cat response.json
```

## Local Development

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Lambda runtime dependencies
pip install -r src/requirements.txt

# Install test dependencies
pip install pytest

# Run tests
pytest
```

## Cost Estimate

All services used have generous free tiers. Rough monthly cost at default settings (10 articles/source, 8 sources):

| Service | Usage | Est. cost/month |
|---|---|---|
| Claude Haiku | ~8k input + ~1.5k output tokens/day | ~$0.12 |
| AWS Lambda | 1 invocation/day, ~2 min runtime | < $0.01 |
| Amazon SES | 1 email/day | < $0.01 |
| Tavily | ~7 requests/day (~210/month) | Free tier |

**Total: ~$0.15/month**

## Project Structure

```
colnews/
├── cdk/
│   ├── app.py               # CDK entry point
│   └── colnews_stack.py     # Stack definition
├── src/
│   ├── handler.py           # Lambda handler (orchestrator)
│   ├── summarizer.py        # Claude API call
│   ├── mailer.py            # SES email sender
│   ├── fetchers/
│   │   ├── __init__.py      # Article dataclass
│   │   ├── base_rss.py      # Shared RSS/Atom parser
│   │   ├── qiita.py
│   │   ├── zenn.py
│   │   ├── hatena.py
│   │   ├── hackernews.py
│   │   ├── reddit.py
│   │   ├── youtube.py
│   │   ├── x_twitter.py     # Tavily-based X/Twitter search
│   │   └── keyword_news.py  # Tavily-based keyword search
│   └── requirements.txt     # Lambda runtime dependencies
├── tests/
├── cdk.json                 # CDK context (configure here)
├── pyproject.toml
└── requirements.txt         # CDK dependencies
```

## License

MIT
