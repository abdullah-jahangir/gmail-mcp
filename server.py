#!/usr/bin/env python3
import asyncio
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from auth import get_gmail_service
from tools import ALL as ALL_TOOLS

server = Server("gmail")


@server.list_tools()
async def list_tools():
    return [tool.definition for tool in ALL_TOOLS]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    service = get_gmail_service()
    for tool in ALL_TOOLS:
        if tool.definition.name == name:
            return tool.execute(arguments, service)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--auth":
        print("Opening browser for Gmail authentication...")
        get_gmail_service()
        print("Authentication successful. Token saved to ~/.gmail-mcp/token.json")
    else:
        asyncio.run(main())
