import boto3


def send_email(subject: str, body_html: str, from_addr: str, to_addrs: list[str]) -> None:
    ses = boto3.client("ses")
    message = {
        "Subject": {"Data": subject, "Charset": "UTF-8"},
        "Body": {"Html": {"Data": body_html, "Charset": "UTF-8"}},
    }
    for addr in to_addrs:
        ses.send_email(
            Source=from_addr,
            Destination={"ToAddresses": [addr]},
            Message=message,
        )
