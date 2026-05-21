#!/usr/bin/env python3
import asyncio
import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

CONFIG_DIR = os.path.expanduser("~/.gmail-mcp")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
TOKEN_FILE = os.path.join(CONFIG_DIR, "token.json")


def get_gmail_service():
    os.makedirs(CONFIG_DIR, exist_ok=True)

    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"credentials.json not found at {CREDENTIALS_FILE}. "
            "Please follow the setup instructions in the README."
        )

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


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


server = Server("gmail")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="send_email",
            description="Send an email via Gmail.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to":                  {"type": "string", "description": "Recipient email address(es), comma-separated"},
                    "subject":             {"type": "string", "description": "Email subject"},
                    "body":                {"type": "string", "description": "Email body (plain text)"},
                    "cc":                  {"type": "string", "description": "CC recipients, comma-separated (optional)"},
                    "bcc":                 {"type": "string", "description": "BCC recipients, comma-separated (optional)"},
                    "reply_to_message_id": {"type": "string", "description": "Message ID to reply to (optional)"},
                },
                "required": ["to", "subject", "body"],
            },
        ),
        Tool(
            name="create_draft",
            description="Create a draft email in Gmail without sending it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to":      {"type": "string"},
                    "subject": {"type": "string"},
                    "body":    {"type": "string"},
                    "cc":      {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        ),
        Tool(
            name="list_emails",
            description="List recent emails from inbox or a specific label.",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "description": "Number of emails to return (default 10)"},
                    "label":       {"type": "string",  "description": "Gmail label (default: INBOX)"},
                },
            },
        ),
        Tool(
            name="search_emails",
            description="Search emails using Gmail query syntax (e.g. 'from:foo@bar.com subject:hello').",
            inputSchema={
                "type": "object",
                "properties": {
                    "query":       {"type": "string",  "description": "Gmail search query"},
                    "max_results": {"type": "integer", "description": "Number of results (default 10)"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_email",
            description="Get the full content of an email by its message ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID"},
                },
                "required": ["message_id"],
            },
        ),
        Tool(
            name="reply_to_email",
            description="Reply to an existing email thread.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "ID of the message to reply to"},
                    "body":       {"type": "string", "description": "Reply body"},
                },
                "required": ["message_id", "body"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    service = get_gmail_service()

    if name == "send_email":
        raw = build_raw_message(
            arguments["to"],
            arguments["subject"],
            arguments["body"],
            arguments.get("cc"),
            arguments.get("bcc"),
            arguments.get("reply_to_message_id"),
        )
        body = {"raw": raw}
        if arguments.get("reply_to_message_id"):
            orig = service.users().messages().get(
                userId="me", id=arguments["reply_to_message_id"], format="metadata"
            ).execute()
            body["threadId"] = orig.get("threadId")
        result = service.users().messages().send(userId="me", body=body).execute()
        return [TextContent(type="text", text=f"Email sent successfully. Message ID: {result['id']}")]

    elif name == "create_draft":
        raw = build_raw_message(arguments["to"], arguments["subject"], arguments["body"], arguments.get("cc"))
        result = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return [TextContent(type="text", text=f"Draft created. Draft ID: {result['id']}")]

    elif name == "list_emails":
        max_results = arguments.get("max_results", 10)
        label = arguments.get("label", "INBOX")
        results = service.users().messages().list(userId="me", labelIds=[label], maxResults=max_results).execute()
        messages = results.get("messages", [])
        if not messages:
            return [TextContent(type="text", text="No emails found.")]
        lines = []
        for msg in messages:
            m = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            h = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
            lines.append(f"ID: {msg['id']}\nFrom: {h.get('From', '')}\nSubject: {h.get('Subject', '')}\nDate: {h.get('Date', '')}")
        return [TextContent(type="text", text="\n\n".join(lines))]

    elif name == "search_emails":
        max_results = arguments.get("max_results", 10)
        results = service.users().messages().list(userId="me", q=arguments["query"], maxResults=max_results).execute()
        messages = results.get("messages", [])
        if not messages:
            return [TextContent(type="text", text="No emails found matching that query.")]
        lines = []
        for msg in messages:
            m = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            h = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
            lines.append(f"ID: {msg['id']}\nFrom: {h.get('From', '')}\nSubject: {h.get('Subject', '')}\nDate: {h.get('Date', '')}")
        return [TextContent(type="text", text="\n\n".join(lines))]

    elif name == "get_email":
        msg = service.users().messages().get(userId="me", id=arguments["message_id"], format="full").execute()
        h = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = extract_body(msg.get("payload", {}))
        text = (
            f"From: {h.get('From', '')}\n"
            f"To: {h.get('To', '')}\n"
            f"Subject: {h.get('Subject', '')}\n"
            f"Date: {h.get('Date', '')}\n\n"
            f"{body}"
        )
        return [TextContent(type="text", text=text)]

    elif name == "reply_to_email":
        orig = service.users().messages().get(
            userId="me", id=arguments["message_id"], format="metadata",
            metadataHeaders=["From", "Subject", "Message-ID"]
        ).execute()
        h = {h["name"]: h["value"] for h in orig.get("payload", {}).get("headers", [])}
        to = h.get("From", "")
        subject = h.get("Subject", "")
        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"
        raw = build_raw_message(to, subject, arguments["body"], reply_to_msg_id=h.get("Message-ID"))
        body = {"raw": raw, "threadId": orig.get("threadId")}
        result = service.users().messages().send(userId="me", body=body).execute()
        return [TextContent(type="text", text=f"Reply sent. Message ID: {result['id']}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--auth":
        print("Opening browser for Gmail authentication...")
        get_gmail_service()
        print("Authentication successful. Token saved to ~/.gmail-mcp/token.json")
    else:
        asyncio.run(main())
