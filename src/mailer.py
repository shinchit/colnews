import boto3


def send_email(subject: str, body_html: str, from_addr: str, to_addrs: list[str]) -> None:
    ses = boto3.client("ses")
    ses.send_email(
        Source=from_addr,
        Destination={"ToAddresses": to_addrs},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {"Html": {"Data": body_html, "Charset": "UTF-8"}},
        },
    )
