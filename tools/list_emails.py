from mcp.types import TextContent, Tool

from utils import get_headers

definition = Tool(
    name="list_emails",
    description="List recent emails from inbox or a specific label.",
    inputSchema={
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Number of emails to return (default 10)"},
            "label":       {"type": "string",  "description": "Gmail label (default: INBOX)"},
        },
    },
)


def execute(arguments: dict, service) -> list[TextContent]:
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
        h = get_headers(m)
        lines.append(f"ID: {msg['id']}\nFrom: {h.get('From', '')}\nSubject: {h.get('Subject', '')}\nDate: {h.get('Date', '')}")
    return [TextContent(type="text", text="\n\n".join(lines))]
