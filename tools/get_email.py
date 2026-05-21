from mcp.types import TextContent, Tool

from utils import extract_body, get_headers

definition = Tool(
    name="get_email",
    description="Get the full content of an email by its message ID.",
    inputSchema={
        "type": "object",
        "properties": {
            "message_id": {"type": "string", "description": "Gmail message ID"},
        },
        "required": ["message_id"],
    },
)


def execute(arguments: dict, service) -> list[TextContent]:
    msg = service.users().messages().get(userId="me", id=arguments["message_id"], format="full").execute()
    h = get_headers(msg)
    body = extract_body(msg.get("payload", {}))
    text = (
        f"From: {h.get('From', '')}\n"
        f"To: {h.get('To', '')}\n"
        f"Subject: {h.get('Subject', '')}\n"
        f"Date: {h.get('Date', '')}\n\n"
        f"{body}"
    )
    return [TextContent(type="text", text=text)]
