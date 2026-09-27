from mcp.server.mcpserver import MCPServer

from tools import (
    read_recent_logs,
    find_log_errors,
    get_application_health,
)


server = MCPServer("System Logs Server")


@server.tool(
    name="read_recent_logs",
    description="Read the most recent application log entries.",
)
def recent_logs(lines: int = 20) -> list[str]:
    return read_recent_logs(lines)


@server.tool(
    name="find_log_errors",
    description="Find application log entries containing errors.",
)
def log_errors() -> list[str]:
    return find_log_errors()


@server.tool(
    name="get_application_health",
    description="Return the current application health based on log activity.",
)
def application_health() -> dict:
    return get_application_health()


if __name__ == "__main__":
    server.run(transport="stdio")