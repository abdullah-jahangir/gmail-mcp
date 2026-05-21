from mcp.types import TextContent, Tool

from utils import build_raw_message

definition = Tool(
    name="create_draft",
    description="Create a draft email in Gmail without sending it.",
    inputSchema={
        "type": "object",
        "properties": {
            "to":      {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject"},
            "body":    {"type": "string", "description": "Email body (plain text)"},
            "cc":      {"type": "string", "description": "CC recipients (optional)"},
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
    )
    result = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return [TextContent(type="text", text=f"Draft created. Draft ID: {result['id']}")]
