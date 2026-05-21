from mcp.types import TextContent, Tool

from utils import build_raw_message

definition = Tool(
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
)


def execute(arguments: dict, service) -> list[TextContent]:
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
