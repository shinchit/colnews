from unittest.mock import patch, MagicMock

from mailer import send_email


def test_send_email_calls_ses():
    with patch("mailer.boto3.client") as mock_boto3:
        mock_ses = MagicMock()
        mock_boto3.return_value = mock_ses

        send_email(
            subject="Test Subject",
            body_html="<html><body>test</body></html>",
            from_addr="from@example.com",
            to_addrs=["to@example.com"],
        )

    mock_boto3.assert_called_once_with("ses")
    mock_ses.send_email.assert_called_once()

    kwargs = mock_ses.send_email.call_args.kwargs
    assert kwargs["Source"] == "from@example.com"
    assert kwargs["Destination"]["ToAddresses"] == ["to@example.com"]
    assert kwargs["Message"]["Subject"]["Data"] == "Test Subject"
    assert "<html>" in kwargs["Message"]["Body"]["Html"]["Data"]


def test_send_email_multiple_recipients():
    with patch("mailer.boto3.client") as mock_boto3:
        mock_ses = MagicMock()
        mock_boto3.return_value = mock_ses

        send_email(
            subject="Test",
            body_html="<p>body</p>",
            from_addr="from@example.com",
            to_addrs=["a@example.com", "b@example.com"],
        )

    kwargs = mock_ses.send_email.call_args.kwargs
    assert len(kwargs["Destination"]["ToAddresses"]) == 2
