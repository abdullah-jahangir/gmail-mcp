import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_raw_message(to, subject, body, cc=None, bcc=None, reply_to_msg_id=None):
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    if reply_to_msg_id:
        msg["In-Reply-To"] = reply_to_msg_id
        msg["References"] = reply_to_msg_id
    msg.attach(MIMEText(body, "plain"))
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")


def extract_body(payload):
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    return ""


def get_headers(message):
    return {h["name"]: h["value"] for h in message.get("payload", {}).get("headers", [])}
