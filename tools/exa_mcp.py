"""
Exa MCP integration via langchain-mcp-adapters.

The Exa MCP server runs as a stdio subprocess — Node.js must be installed.
Falls back to direct exa-py SDK if MCP server is unavailable.
"""

import os
import asyncio
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

EXA_API_KEY = os.getenv("EXA_API_KEY", "")


# ── Primary: Exa via MCP (adds genuine MCP experience to resume) ─────────────

async def get_exa_mcp_tools():
    """
    Connects to the Exa MCP server via stdio and returns LangChain-compatible tools.
    Requires: npm install -g exa-mcp-server  (once)
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient({
        "exa": {
            "command": "npx",
            "args": ["exa-mcp-server"],
            "env": {"EXA_API_KEY": EXA_API_KEY},
            "transport": "stdio",
        }
    })

    tools = await client.get_tools()
    return tools, client


# ── Fallback: direct exa-py SDK wrapped as LangChain tool ────────────────────

def get_exa_direct_tools():
    """
    Direct Exa Python SDK as LangChain tools — no Node.js needed.
    Use this if MCP server setup is not available.
    """
    from langchain_core.tools import tool
    from exa_py import Exa

    exa = Exa(api_key=EXA_API_KEY)

    @tool
    def exa_search(query: str, num_results: int = 5) -> str:
        """Search for job postings using Exa neural search."""
        results = exa.search(
            query, num_results=num_results)
        return "\n\n".join(
            f"Title: {r.title}\nURL: {r.url}\nSummary: {getattr(r, 'text', '')[:500]}"
            for r in results.results
        )

    @tool
    def exa_fetch_url(url: str) -> str:
        """Fetch the full content of a job posting URL using Exa."""
        result = exa.get_contents([url], text=True)
        if result.results:
            return result.results[0].text or "No content returned"
        return "Failed to fetch URL"

    return [exa_search, exa_fetch_url]


def get_tools(use_mcp: bool = True):
    """
    Returns Exa tools. Prefers MCP; falls back to direct SDK.
    Set use_mcp=False to skip MCP and use the SDK directly.
    """
    if use_mcp:
        try:
            tools, client = asyncio.get_event_loop().run_until_complete(
                get_exa_mcp_tools()
            )
            print("✅ Exa MCP server connected")
            return tools
        except Exception as e:
            print(f"⚠️  Exa MCP unavailable ({e}), falling back to direct SDK")

    return get_exa_direct_tools()
