import os

import aws_cdk as cdk
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_secretsmanager as secretsmanager
from aws_cdk import aws_lambda_python_alpha as python_lambda
from constructs import Construct


class ColnewsStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ctx = self.node
        anthropic_secret_name = ctx.try_get_context("anthropic_secret_name") or "colnews/anthropic-api-key"
        tavily_secret_name = ctx.try_get_context("tavily_secret_name") or "colnews/tavily-api-key"
        ses_from = ctx.try_get_context("ses_from_address") or ""
        to_addresses = ctx.try_get_context("to_addresses") or ""
        yt_channels = ctx.try_get_context("youtube_channel_ids") or ""
        reddit_subs = ctx.try_get_context("reddit_subreddits") or "programming,tech"
        keywords = ctx.try_get_context("search_keywords") or "AI,LLM,AWS,TypeScript,Claude,Gemini"

        anthropic_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "AnthropicSecret", anthropic_secret_name
        )
        tavily_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "TavilySecret", tavily_secret_name
        )

        entry_path = os.path.join(os.path.dirname(__file__), "..", "src")

        news_fn = python_lambda.PythonFunction(
            self,
            "ColnewsFunction",
            entry=entry_path,
            runtime=lambda_.Runtime.PYTHON_3_12,
            index="handler.py",
            handler="main",
            architecture=lambda_.Architecture.ARM_64,
            timeout=cdk.Duration.minutes(5),
            memory_size=512,
            environment={
                "ANTHROPIC_SECRET_ARN": anthropic_secret.secret_arn,
                "TAVILY_SECRET_ARN": tavily_secret.secret_arn,
                "SES_FROM_ADDRESS": ses_from,
                "TO_ADDRESSES": to_addresses,
                "MAX_ITEMS_PER_SOURCE": "10",
                "CLAUDE_MODEL": "claude-haiku-4-5-20251001",
                "YOUTUBE_CHANNEL_IDS": yt_channels,
                "REDDIT_SUBREDDITS": reddit_subs,
                "SEARCH_KEYWORDS": keywords,
            },
        )

        anthropic_secret.grant_read(news_fn)
        tavily_secret.grant_read(news_fn)

        news_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"],
            )
        )

        rule = events.Rule(
            self,
            "ColnewsSchedule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="21",
                day="*",
                month="*",
                year="*",
            ),
        )
        rule.add_target(targets.LambdaFunction(news_fn))
