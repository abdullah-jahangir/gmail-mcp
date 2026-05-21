from mcp.types import TextContent, Tool

from utils import get_headers

definition = Tool(
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
)


def execute(arguments: dict, service) -> list[TextContent]:
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
        h = get_headers(m)
        lines.append(f"ID: {msg['id']}\nFrom: {h.get('From', '')}\nSubject: {h.get('Subject', '')}\nDate: {h.get('Date', '')}")
    return [TextContent(type="text", text="\n\n".join(lines))]
