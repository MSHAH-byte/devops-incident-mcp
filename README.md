# DevOps Incident Response MCP

A multi-server Model Context Protocol (MCP) system for AI-assisted DevOps incident investigation.

The system connects a central AI agent to independent MCP servers for application logs and GitHub. The agent dynamically discovers available tools, selects relevant tools during an investigation, analyzes the collected evidence, and can propose a GitHub issue. GitHub issue creation requires explicit human approval.

## Overview

This project demonstrates how MCP can connect an AI agent to multiple independent tool servers while keeping external actions controlled by a human.

The system currently contains two MCP servers:

* **System Logs MCP Server** — analyzes application logs and application health.
* **GitHub MCP Server** — retrieves repository activity and can create GitHub issues.

The central agent communicates with both servers over **MCP stdio transport**.

## Architecture

```text
                         ┌──────────────────────────┐
                         │       Central AI Agent   │
                         │                          │
                         │  • Tool discovery        │
                         │  • Tool selection        │
                         │  • Investigation         │
                         │  • Evidence analysis     │
                         │  • Issue proposal        │
                         └────────────┬─────────────┘
                                      │
                              MCP stdio
                         ┌────────────┴────────────┐
                         │                         │
                         ▼                         ▼
              ┌─────────────────────┐   ┌─────────────────────┐
              │ System Logs Server   │   │ GitHub Server       │
              │                     │   │                     │
              │ read_recent_logs    │   │ get_recent_commits  │
              │ find_log_errors     │   │ get_open_pull_      │
              │ get_application_    │   │ requests             │
              │ health              │   │ create_bug_issue    │
              └─────────────────────┘   └─────────────────────┘
```

## Investigation Flow

```text
User selects investigation
          ↓
Central agent receives request
          ↓
MCP tools are discovered dynamically
          ↓
LLM selects relevant read-only tools
          ↓
Tools are executed on the appropriate MCP servers
          ↓
Evidence is returned to the agent
          ↓
LLM produces an investigation
          ↓
LLM determines whether an issue should be proposed
          ↓
Issue title and body are shown to the user
          ↓
Human approval
      ↙          ↘
    Yes           No
     ↓             ↓
GitHub issue     Cancel
created
          ↓
Return to menu
```

## MCP Servers

### 1. System Logs MCP Server

Location:

```text
servers/logs_server/
```

Tools:

#### `read_recent_logs`

Returns the most recent application log entries.

Example:

```text
read_recent_logs(lines=20)
```

#### `find_log_errors`

Returns application log entries containing `ERROR`.

#### `get_application_health`

Returns a health summary based on the application logs, including:

* Overall application status
* Error count
* Warning count
* Payment service status

### 2. GitHub MCP Server

Location:

```text
servers/github_server/
```

Tools:

#### `get_recent_commits`

Returns recent commits from the configured GitHub repository.

#### `get_open_pull_requests`

Returns currently open pull requests.

#### `create_bug_issue`

Creates a GitHub issue in the configured repository.

This is a **write operation** and is only executed after explicit human approval.

## Central AI Agent

Location:

```text
agent/
```

### `agent.py`

Contains the central agent implementation.

Responsibilities include:

* Connecting to both MCP servers
* Discovering MCP tools
* Converting MCP tool definitions for the LLM
* Dynamically selecting tools
* Executing tool calls
* Combining evidence from multiple MCP servers
* Producing incident analysis
* Preparing GitHub issue proposals
* Requesting human approval before GitHub writes

### `main.py`

Application entry point.

Run the agent with:

```powershell
python .\agent\main.py
```

## Interactive Menu

When the application starts, it provides:

```text
1. Check application health
2. Find application errors
3. Investigate a specific incident
4. Review recent GitHub activity
5. Check open pull requests
6. Full incident investigation
7. Exit
```

The application remains active until the user selects **7. Exit**.

## Example Investigation

A user can select option 3 and provide:

```text
Payment requests are failing. Investigate what is causing the payment service failure and check whether recent GitHub changes might be related.
```

The agent can dynamically select tools such as:

```text
find_log_errors
read_recent_logs
get_recent_commits
get_open_pull_requests
```

The exact order depends on the investigation and is selected by the LLM rather than being implemented as a fixed investigation sequence.

## Human-in-the-Loop

The GitHub write operation is intentionally separated from the read-only investigation tools.

The agent does not automatically create an issue.

Instead, it produces an issue proposal:

```text
GITHUB ISSUE PROPOSAL

Title:
...

Body:
...

Create this GitHub issue?
1. Yes
2. No
```

Only after selecting **Yes** does the application call:

```text
create_bug_issue
```

This demonstrates controlled AI actions where potentially consequential external operations require human approval.

## Project Structure

```text
DevOps_Incident_MCP/
│
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
├── .env
├── .env.example
│
├── agent/
│   ├── agent.py
│   └── main.py
│
├── servers/
│   ├── github_server/
│   │   ├── server.py
│   │   └── tools.py
│   │
│   └── logs_server/
│       ├── server.py
│       └── tools.py
│
└── logs/
    └── application.log
```

## Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/your_repository
```

For example:

```env
GITHUB_REPO=MSHAH-byte/web_project
```

Do **not** commit `.env` or any API keys to GitHub.

A `.env.example` file can be used as the safe configuration template.

## GitHub Token Permissions

The GitHub token should use the minimum permissions required by the project.

For the configured repository, the project requires:

* Contents: Read-only
* Pull requests: Read-only
* Issues: Read and write

Repository access should be limited to the repository being used for testing.

## Installation

Create and activate a Python virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Running the Project

From the project root:

```powershell
python .\agent\main.py
```

The central agent starts both MCP servers, discovers their tools, and displays the interactive menu.

## Technologies

* Python
* Model Context Protocol (MCP)
* MCP Python SDK
* Groq API
* OpenAI-compatible tool calling
* Pydantic
* Requests
* python-dotenv
* GitHub REST API
* MCP stdio transport
* SQLite/application log data

## MCP Concepts Demonstrated

This project focuses on practical MCP concepts:

* MCP hosts and clients
* Independent MCP servers
* MCP tool definitions
* Dynamic tool discovery
* Tool schemas
* MCP stdio transport
* Multiple MCP servers
* LLM tool calling
* Tool routing
* Read-only versus write tools
* Human-in-the-loop approval
* External side effects
* AI-assisted incident investigation

## Learning Progression

This project builds on the previous MCP database project.

### Project 1 — Database Inspection MCP Server

Demonstrated:

```text
AI/MCP Client
      ↓
SQLite MCP Server
      ↓
Database inspection and read-only queries
```

### Project 2 — DevOps Incident Response MCP

Expands the architecture to:

```text
                    AI Agent
                       ↓
              Dynamic Tool Discovery
                  ↙         ↘
                 ↓           ↓
          Logs MCP       GitHub MCP
             Server         Server
                 ↘         ↙
                    Evidence
                       ↓
                 AI Analysis
                       ↓
                Human Approval
                       ↓
                 GitHub Issue
```

This progression demonstrates how MCP can scale from a single tool server to multiple independent servers coordinated by an AI agent.

## Security Considerations

* API keys are loaded from environment variables.
* `.env` is excluded from version control.
* GitHub write operations require explicit human approval.
* Read-only investigation tools are separated from write-capable tools.
* The GitHub token should be restricted to the required repository and permissions.

## Purpose

The purpose of this project is to understand and implement MCP in a realistic agent workflow rather than building a production-grade DevOps platform.

The emphasis is on:

* Understanding MCP architecture
* Building independent MCP servers
* Connecting multiple servers to one agent
* Letting the LLM select tools dynamically
* Handling real external actions safely
* Demonstrating human oversight of consequential operations
