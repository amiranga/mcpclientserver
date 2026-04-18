import argparse
import asyncio
import json
from pathlib import Path

from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "meta-llama/Llama-3.1-8B-Instruct:cerebras"
HF_TOKEN = "TOKEN"

SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Use available tools when needed. "
    "If the question is unrelated to the tools, answer normally."
)


def build_llm_client() -> OpenAI:
    return OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)


def mcp_tools_to_llm_tools(mcp_tools):
    llm_tools = []
    for tool in mcp_tools:
        llm_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema or {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            }
        )
    return llm_tools


async def run(query: str) -> None:
    server_script = str(Path(__file__).with_name("server.py"))
    server_params = StdioServerParameters(command="python", args=[server_script])
    llm = build_llm_client()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            mcp_response = await session.list_tools()
            mcp_tools = mcp_response.tools
            llm_tools = mcp_tools_to_llm_tools(mcp_tools)

            print("Available MCP tools:")
            for tool in mcp_tools:
                print(f"- {tool.name}: {tool.description}")

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ]

            first = llm.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=llm_tools,
                tool_choice="auto",
                temperature=0.1,
            )

            message = first.choices[0].message
            tool_calls = message.tool_calls or []

            if not tool_calls:
                print("\nFinal answer:\n", message.content)
                return

            messages.append(message.model_dump(exclude_none=True))

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments or "{}")

                print(f"\nCalling MCP tool: {tool_name} with args {tool_args}")
                result = await session.call_tool(tool_name, tool_args)
                tool_text = "\n".join(getattr(item, "text", str(item)) for item in result.content)

                print("\nMCP tool result:\n", tool_text)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_text,
                    }
                )

            final = llm.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=llm_tools,
                temperature=0.1,
            )

            print("\nFinal answer:\n", final.choices[0].message.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dynamic MCP-to-LLM tool bridge client")
    parser.add_argument("query", nargs="?", default="Who is Rick characters in Rick and Morty?")
    args = parser.parse_args()
    asyncio.run(run(args.query))