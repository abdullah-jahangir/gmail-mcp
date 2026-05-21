from mcp.types import TextContent, Tool

from utils import build_raw_message, get_headers

definition = Tool(
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
)


def execute(arguments: dict, service) -> list[TextContent]:
    orig = service.users().messages().get(
        userId="me", id=arguments["message_id"], format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID"]
    ).execute()
    h = get_headers(orig)
    subject = h.get("Subject", "")
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"
    raw = build_raw_message(h.get("From", ""), subject, arguments["body"], reply_to_msg_id=h.get("Message-ID"))
    body = {"raw": raw, "threadId": orig.get("threadId")}
    result = service.users().messages().send(userId="me", body=body).execute()
    return [TextContent(type="text", text=f"Reply sent. Message ID: {result['id']}")]
