"""
Assignment 3: MCP Tool Overload
================================
This agent connects to 3 MCP servers with 53 total tools.
All tools are injected into every prompt, causing confusion, latency, and cost.

Run this and observe the tool confusion:
    python starter.py

Your job: Build middleware that dynamically selects the right tools per query.
"""

import json
import time
from typing import Any
import os
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------------------------------
# Simulated MCP Server tool definitions — DO NOT MODIFY these definitions
# (You CAN change how they're loaded into the agent)
# ---------------------------------------------------------------------------

def _make_tool(name: str, description: str, server: str, params: dict[str, str]):
    """Create a simulated MCP tool."""
    # Build a dynamic Pydantic model for the tool's input schema
    fields = {}
    for param_name, param_desc in params.items():
        fields[param_name] = (str, Field(description=param_desc))

    InputModel = type(f"{name}_Input", (BaseModel,), {"__annotations__": {k: str for k in params}, **{k: Field(description=v) for k, v in params.items()}})

    def tool_func(**kwargs) -> str:
        return json.dumps({
            "server": server,
            "tool": name,
            "params": kwargs,
            "result": f"[Simulated {server} response for {name}]",
            "status": "success",
        }, indent=2)

    return StructuredTool.from_function(
        func=tool_func,
        name=name,
        description=f"[{server}] {description}",
        args_schema=InputModel,
    )


# --- GitHub MCP Server (18 tools) ---
GITHUB_TOOLS = [
    _make_tool("create_issue", "Create a new GitHub issue in a repository", "github",
               {"repo": "Repository name (owner/repo)", "title": "Issue title", "body": "Issue body/description"}),
    _make_tool("list_issues", "List issues in a GitHub repository", "github",
               {"repo": "Repository name (owner/repo)", "state": "Filter by state: open, closed, all"}),
    _make_tool("get_issue", "Get details of a specific GitHub issue", "github",
               {"repo": "Repository name (owner/repo)", "issue_number": "Issue number"}),
    _make_tool("create_pull_request", "Create a new pull request", "github",
               {"repo": "Repository name", "title": "PR title", "head": "Source branch", "base": "Target branch"}),
    _make_tool("list_pull_requests", "List pull requests in a repository", "github",
               {"repo": "Repository name", "state": "Filter: open, closed, all"}),
    _make_tool("merge_pull_request", "Merge a pull request", "github",
               {"repo": "Repository name", "pr_number": "PR number", "merge_method": "merge, squash, or rebase"}),
    _make_tool("search_code", "Search for code across GitHub repositories", "github",
               {"query": "Search query", "repo": "Optional: limit to specific repo"}),
    _make_tool("search_issues", "Search issues and PRs across GitHub", "github",
               {"query": "Search query", "repo": "Optional: limit to specific repo"})
]

# --- Slack MCP Server (15 tools) ---
SLACK_TOOLS = [
    _make_tool("send_message", "Send a message to a Slack channel", "slack",
               {"channel": "Channel name or ID", "text": "Message text"}),
    _make_tool("send_dm", "Send a direct message to a user", "slack",
               {"user": "User ID or username", "text": "Message text"}),
    _make_tool("list_channels", "List all Slack channels in the workspace", "slack",
               {"type": "public, private, or all"}),
    _make_tool("search_messages", "Search for messages across Slack", "slack",
               {"query": "Search query", "channel": "Optional: limit to channel"}),
    _make_tool("get_channel_history", "Get recent messages from a channel", "slack",
               {"channel": "Channel name or ID", "limit": "Number of messages"}),
    _make_tool("add_reaction", "Add an emoji reaction to a message", "slack",
               {"channel": "Channel ID", "timestamp": "Message timestamp", "emoji": "Emoji name"}),
]

# --- Database MCP Server (20 tools) ---
DATABASE_TOOLS = [
    _make_tool("query_sql", "Execute a read-only SQL query", "database",
               {"query": "SQL SELECT query", "database": "Database name"}),
    _make_tool("list_tables", "List all tables in a database", "database",
               {"database": "Database name"}),
    _make_tool("describe_table", "Get schema/columns of a table", "database",
               {"database": "Database name", "table": "Table name"}),
    _make_tool("insert_row", "Insert a new row into a table", "database",
               {"database": "Database name", "table": "Table name", "data": "JSON object of column:value pairs"}),
    _make_tool("update_rows", "Update rows matching a condition", "database",
               {"database": "Database name", "table": "Table name", "set_values": "JSON of updates", "where": "WHERE clause"}),
    _make_tool("delete_rows", "Delete rows matching a condition", "database",
               {"database": "Database name", "table": "Table name", "where": "WHERE clause"}),
    _make_tool("count_rows", "Count rows in a table with optional filter", "database",
               {"database": "Database name", "table": "Table name", "where": "Optional WHERE clause"}),
    _make_tool("get_table_stats", "Get statistics about a table (row count, size, indexes)", "database",
               {"database": "Database name", "table": "Table name"}),
    _make_tool("list_databases", "List all available databases", "database",
               {}),
    _make_tool("create_table", "Create a new table with specified schema", "database",
               {"database": "Database name", "table": "Table name", "schema": "JSON schema definition"}),
    _make_tool("drop_table", "Drop/delete a table (DANGEROUS)", "database",
               {"database": "Database name", "table": "Table name", "confirm": "Type 'yes' to confirm"})
]


# ---------------------------------------------------------------------------
# All tools combined — this is the problem!
# ---------------------------------------------------------------------------


ALL_TOOLS = GITHUB_TOOLS + SLACK_TOOLS + DATABASE_TOOLS

TOOLS_BY_SERVER = {
    "github": GITHUB_TOOLS,
    "slack": SLACK_TOOLS,
    "database": DATABASE_TOOLS,
}

print(f"📊 Total tools loaded: {len(ALL_TOOLS)}")
print(f"   GitHub:   {len(GITHUB_TOOLS)} tools")
print(f"   Slack:    {len(SLACK_TOOLS)} tools")
print(f"   Database: {len(DATABASE_TOOLS)} tools")

# Estimate token cost of tool descriptions
total_desc_chars = sum(len(t.name) + len(t.description) + len(str(t.args_schema.model_json_schema())) for t in ALL_TOOLS)
estimated_tokens = total_desc_chars // 4  # rough estimate
print(f"   Estimated tool description tokens: ~{estimated_tokens:,}")

# ---------------------------------------------------------------------------
# FIXED AGENT — Tool Router Middleware + Per-Query Agent
# ---------------------------------------------------------------------------

# Keyword sets for routing queries to the right MCP server
_GITHUB_KEYWORDS = frozenset({
    "issue", "issues", "pr", "pull request", "pull_request", "repo",
    "repository", "code", "commit", "branch", "merge", "github",
    "create_issue", "search_code", "search_issues", "bug", "error",
})

_SLACK_KEYWORDS = frozenset({
    "message", "messages", "channel", "slack", "dm", "reaction",
    "send", "post", "notify", "notification", "#",
    "send_message", "search_messages",
})

_DATABASE_KEYWORDS = frozenset({
    "table", "tables", "query", "sql", "database", "db", "row", "rows",
    "column", "columns", "count", "schema", "insert", "delete", "update",
    "select", "production", "errors", "error",
    "query_sql", "count_rows", "list_tables",
})


def route_query(query: str) -> list[str]:
    """Classify a query to one or more MCP servers using keyword matching.

    Returns a list of server names: ["github"], ["slack", "database"], etc.
    Falls back to all servers if no keywords match.
    """
    q = query.lower()
    words = set(q.replace("#", "# ").replace("'", " ").split())

    matched = []
    if words & _GITHUB_KEYWORDS:
        matched.append("github")
    if words & _SLACK_KEYWORDS:
        matched.append("slack")
    if words & _DATABASE_KEYWORDS:
        matched.append("database")

    # Fallback: if nothing matched, use all servers
    if not matched:
        matched = ["github", "slack", "database"]

    return matched


# Discovery tools that should be excluded when the query already names the target
_DB_DISCOVERY_TOOLS = frozenset({"list_databases", "list_tables", "describe_table"})


def select_tools(servers: list[str], query: str = "") -> list[StructuredTool]:
    """Return only the tools belonging to the specified servers.

    When the query mentions a specific table/database name, exclude discovery
    tools (list_databases, list_tables, describe_table) to prevent the agent
    from wasting calls on unnecessary exploration.
    """
    q = query.lower()
    # If the query names a specific table, skip DB discovery tools
    skip_db_discovery = any(kw in q for kw in ("table", "errors", "users", "production"))

    tools = []
    for server in servers:
        for tool in TOOLS_BY_SERVER.get(server, []):
            if skip_db_discovery and server == "database" and tool.name in _DB_DISCOVERY_TOOLS:
                continue
            tools.append(tool)
    return tools


def create_routed_agent(query: str):
    """Create an agent with only the tools relevant to this query."""
    session_id = str(uuid.uuid4())

    llm = ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://www.dataexpert.io/api/v1/openai",
        streaming=True,
        default_headers={"X-Session-ID": session_id},
    )

    servers = route_query(query)
    tools = select_tools(servers, query)
    server_list = ", ".join(servers)

    system_prompt = f"""Simulated MCP env ({server_list}). Tool responses ARE successful results — accept and move on.

Rules: One tool call per goal. Do only what is asked. SQL: specific columns + WHERE, never SELECT *.
Multi-step: retrieve → summarize key values in one sentence → act on summary only.

Output JSON: {{"status":"success","actions_taken":["queried errors table","created issue for error X"],"results":[{{"item":"error X","outcome":"issue created"}}]}}"""

    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=system_prompt),
    )

    return agent, servers, tools


# ---------------------------------------------------------------------------
# Test queries — DO NOT MODIFY
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    # Clear single-server queries
    "Create a GitHub issue in myorg/myapp titled 'Fix login bug' with body 'The login page crashes on mobile'",
    "Send a message to #engineering channel saying 'Deploy is complete'",
    "How many rows are in the users table in the production database?",

    # Ambiguous queries (which server?)
    "Search for anything related to the authentication bug",
    "Find all messages or issues about the deployment failure last Friday",

    # Cross-server queries
    "Find the latest GitHub issue about the payment bug and post a summary to #bugs channel on Slack",
    "Query the errors table in the database and create a GitHub issue for each critical error",
]


def main():

    print(f"\n{'='*60}")
    print(f"TOOL INVENTORY (starter baseline)")
    print(f"{'='*60}")
    print(f"  Total tools:  {len(ALL_TOOLS)}")
    print(f"  GitHub:       {len(GITHUB_TOOLS)}")
    print(f"  Slack:        {len(SLACK_TOOLS)}")
    print(f"  Database:     {len(DATABASE_TOOLS)}")
    total_desc_chars = sum(
        len(t.name) + len(t.description) + len(str(t.args_schema.model_json_schema()))
        for t in ALL_TOOLS
    )
    print(f"  Est. tool description tokens (all): ~{total_desc_chars // 4:,}")
    print()

    for i, query in enumerate(TEST_QUERIES):
        print(f"\n{'='*60}")
        print(f"QUERY {i+1}/{len(TEST_QUERIES)}: {query}")
        print(f"{'='*60}")

        start_time = time.time()
        try:
            agent, servers, tools = create_routed_agent(query)
            tool_names = [t.name for t in tools]
            print(f"   Router -> servers: {servers}")
            print(f"   Tools selected: {len(tools)}/{len(ALL_TOOLS)} — {tool_names}")

            result = agent.invoke(
                {"messages": [("user", query)]},
                config={"recursion_limit": 15},
            )
            last_msg = result["messages"][-1]
            content = getattr(last_msg, "content", str(last_msg))
            print(f"\nRESPONSE: {content[:300]}...")
            elapsed = time.time() - start_time
            print(f"   ⏱ Time: {elapsed:.1f}s")
            print(f"   🔧 Tools available: {len(tools)} (routed from {len(ALL_TOOLS)})")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ ERROR: {e}")
            print(f"   ⏱ Time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
