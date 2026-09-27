import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from mcp import Client, StdioServerParameters


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


LOGS_SERVER = StdioServerParameters(
    command="python",
    args=[str(PROJECT_ROOT / "servers" / "logs_server" / "server.py")],
)

GITHUB_SERVER = StdioServerParameters(
    command="python",
    args=[str(PROJECT_ROOT / "servers" / "github_server" / "server.py")],
)


WRITE_TOOLS = {"create_bug_issue"}


def extract_text(result) -> list[str]:
    return [
        item.text
        for item in result.content
        if hasattr(item, "text")
    ]


async def discover_tools(client: Client) -> list[dict]:
    result = await client.list_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.input_schema,
        }
        for tool in result.tools
    ]


async def call_tool(
    client: Client,
    tool_name: str,
    arguments: dict,
) -> str:
    result = await client.call_tool(tool_name, arguments)
    return "\n".join(extract_text(result))


def convert_mcp_tools_to_groq(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }
        for tool in tools
        if tool["name"] not in WRITE_TOOLS
    ]


def get_client_for_tool(
    tool_name: str,
    logs_client: Client,
    github_client: Client,
) -> Client:

    if tool_name in {
        "read_recent_logs",
        "find_log_errors",
        "get_application_health",
    }:
        return logs_client

    if tool_name in {
        "get_recent_commits",
        "get_open_pull_requests",
        "create_bug_issue",
    }:
        return github_client

    raise ValueError(f"Unknown MCP tool: {tool_name}")


async def run_agent(
    user_request: str,
    logs_client: Client,
    github_client: Client,
    all_tools: list[dict],
) -> dict:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    groq_client = Groq(api_key=api_key)

    available_tools = convert_mcp_tools_to_groq(all_tools)

    messages = [
        {
            "role": "system",
            "content": """
You are a DevOps incident investigation agent.

You have access to read-only MCP tools from:
- System Logs MCP Server
- GitHub MCP Server

Investigate the user's request using only the tools that are
actually relevant.

Choose tools dynamically. Do not blindly call every tool.

Do not invent evidence.
Do not claim something is confirmed unless the available evidence
supports it.

When investigation is complete, return a JSON object with exactly:

{
  "analysis": "complete investigation in clear markdown",
  "should_create_issue": true or false,
  "issue_title": "short issue title or empty string",
  "issue_body": "detailed GitHub issue body or empty string"
}

Only set should_create_issue to true when the evidence indicates
that creating an issue is appropriate.

The issue must NOT be created by you.
The application will ask the human for approval before performing
the GitHub write operation.
""",
        },
        {
            "role": "user",
            "content": user_request,
        },
    ]

    for _ in range(8):

        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=available_tools,
            tool_choice="auto",
            temperature=0.1,
        )

        message = response.choices[0].message

        if not message.tool_calls:

            content = message.content or ""

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "analysis": content,
                    "should_create_issue": False,
                    "issue_title": "",
                    "issue_body": "",
                }

        messages.append(
            message.model_dump(exclude_none=True)
        )

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )
            except json.JSONDecodeError:
                arguments = {}

            print(
                f"\n[Agent] Calling MCP tool: {tool_name}"
            )
            print(
                f"[Agent] Arguments: {arguments}"
            )

            client = get_client_for_tool(
                tool_name,
                logs_client,
                github_client,
            )

            result = await call_tool(
                client,
                tool_name,
                arguments,
            )

            print("[Agent] MCP result received.")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return {
        "analysis": "Investigation reached the maximum number of tool calls.",
        "should_create_issue": False,
        "issue_title": "",
        "issue_body": "",
    }


async def create_issue_with_approval(
    github_client: Client,
    title: str,
    body: str,
) -> None:

    print("\n" + "=" * 60)
    print("GITHUB ISSUE PROPOSAL")
    print("=" * 60)

    print(f"\nTitle:\n{title}")
    print(f"\nBody:\n{body}")

    print("\nCreate this GitHub issue?")
    print("1. Yes")
    print("2. No")

    choice = input("\nSelect: ").strip()

    if choice != "1":
        print("\nIssue creation cancelled.")
        return

    result = await call_tool(
        github_client,
        "create_bug_issue",
        {
            "title": title,
            "body": body,
        },
    )

    print("\n" + "=" * 60)
    print("GITHUB ISSUE CREATED")
    print("=" * 60)
    print(result)


def print_menu() -> None:

    print("\n" + "=" * 50)
    print("       DEVOPS INCIDENT RESPONSE AGENT")
    print("=" * 50)

    print("\nWhat would you like to investigate?\n")

    print("1. Check application health")
    print("2. Find application errors")
    print("3. Investigate a specific incident")
    print("4. Review recent GitHub activity")
    print("5. Check open pull requests")
    print("6. Full incident investigation")
    print("7. Exit")


async def investigate(
    request: str,
    logs_client: Client,
    github_client: Client,
    all_tools: list[dict],
) -> None:

    print("\n=== AI INVESTIGATION ===")

    result = await run_agent(
        request,
        logs_client,
        github_client,
        all_tools,
    )

    print("\n=== INVESTIGATION RESULT ===")
    print(result["analysis"])

    if result.get("should_create_issue"):

        print("\nThe agent recommends creating a GitHub issue.")

        await create_issue_with_approval(
            github_client,
            result["issue_title"],
            result["issue_body"],
        )

    else:
        print("\nNo GitHub issue was proposed.")


async def main() -> None:

    async with Client(LOGS_SERVER) as logs_client:

        async with Client(GITHUB_SERVER) as github_client:

            logs_tools = await discover_tools(logs_client)
            github_tools = await discover_tools(github_client)

            all_tools = logs_tools + github_tools

            print(
                f"\nDiscovered {len(all_tools)} MCP tools "
                "across 2 servers."
            )

            while True:

                print_menu()

                choice = input("\nSelect an option: ").strip()

                if choice == "7":
                    print("\nGoodbye.")
                    break

                elif choice == "1":

                    result = await call_tool(
                        logs_client,
                        "get_application_health",
                        {},
                    )

                    print("\n=== APPLICATION HEALTH ===")
                    print(result)

                elif choice == "2":

                    result = await call_tool(
                        logs_client,
                        "find_log_errors",
                        {},
                    )

                    print("\n=== APPLICATION ERRORS ===")
                    print(result)

                elif choice == "3":

                    incident = input(
                        "\nDescribe the incident:\n> "
                    ).strip()

                    if not incident:
                        print(
                            "\nIncident description cannot be empty."
                        )
                        continue

                    await investigate(
                        incident,
                        logs_client,
                        github_client,
                        all_tools,
                    )

                elif choice == "4":

                    result = await call_tool(
                        github_client,
                        "get_recent_commits",
                        {"limit": 10},
                    )

                    print("\n=== RECENT GITHUB COMMITS ===")
                    print(result)

                elif choice == "5":

                    result = await call_tool(
                        github_client,
                        "get_open_pull_requests",
                        {},
                    )

                    print("\n=== OPEN PULL REQUESTS ===")
                    print(result)

                elif choice == "6":

                    await investigate(
                        """
Perform a comprehensive incident investigation.

Determine the current application problem using the available
evidence, identify likely causes, assess impact, check relevant
GitHub activity, and determine whether a GitHub issue should be
created.
""",
                        logs_client,
                        github_client,
                        all_tools,
                    )

                else:
                    print(
                        "\nInvalid option. Please select 1-7."
                    )