import asyncio
import json
from typing import Any

import httpx
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

API_URL = "https://rickandmortyapi.com/api/character"
server = Server("rick-and-morty-mcp-server")


async def fetch_all_characters() -> list[dict[str, Any]]:
    characters: list[dict[str, Any]] = []
    next_url: str | None = API_URL
    async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": "mcp-rick-morty-demo/1.0"}) as client:
        while next_url:
            response = await client.get(next_url)
            response.raise_for_status()
            payload = response.json()
            characters.extend(payload.get("results", []))
            next_url = payload.get("info", {}).get("next")
    return characters


async def search_characters(name: str) -> list[dict[str, Any]]:
    all_characters = await fetch_all_characters()
    q = name.strip().lower()
    return [c for c in all_characters if q in c.get("name", "").lower()]


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="find_rick_and_morty_character",
            description="Find Rick and Morty characters by name and return their profile details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full or partial character name, for example Rick, Morty, Summer, or Birdperson.",
                    }
                },
                "required": ["name"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    if name != "find_rick_and_morty_character":
        raise ValueError(f"Unknown tool: {name}")

    query = str(arguments.get("name", "")).strip()
    if not query:
        return [types.TextContent(type="text", text="Please provide a character name.")]

    matches = await search_characters(query)
    if not matches:
        return [types.TextContent(type="text", text=f"No Rick and Morty characters found for '{query}'.")]

    slim = []
    for c in matches[:10]:
        slim.append(
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "status": c.get("status"),
                "species": c.get("species"),
                "type": c.get("type"),
                "gender": c.get("gender"),
                "origin": c.get("origin", {}).get("name"),
                "location": c.get("location", {}).get("name"),
                "episode_count": len(c.get("episode", [])),
                "image": c.get("image"),
                "url": c.get("url"),
            }
        )

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "query": query,
                    "match_count": len(matches),
                    "matches": slim,
                },
                indent=2,
            ),
        )
    ]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="rick-and-morty-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
