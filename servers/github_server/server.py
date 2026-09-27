from mcp.server.mcpserver import MCPServer

from tools import (
    get_recent_commits,
    get_open_pull_requests,
    create_bug_issue,
)


server = MCPServer("GitHub Management Server")


@server.tool(
    name="get_recent_commits",
    description="Get recent commits from the configured GitHub repository.",
)
def recent_commits(limit: int = 10) -> list[dict]:
    return get_recent_commits(limit)


@server.tool(
    name="get_open_pull_requests",
    description="Get currently open pull requests from the configured GitHub repository.",
)
def open_pull_requests() -> list[dict]:
    return get_open_pull_requests()


@server.tool(
    name="create_bug_issue",
    description="Create a bug issue in the configured GitHub repository. This performs a real write operation.",
)
def bug_issue(title: str, body: str) -> dict:
    return create_bug_issue(title, body)


if __name__ == "__main__":
    server.run(transport="stdio")