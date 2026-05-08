"""GitHub Repo Tracker — MCP server with a Prefab UI dashboard.

Tools exposed:
  - track_repo(owner, name, notes="")      fetch live GitHub stats and save
  - untrack_repo(owner, name)              remove from tracked_repos.json
  - update_repo_notes(owner, name, notes)  edit notes for a tracked repo
  - refresh_repo(owner, name)              re-fetch live stats
  - list_tracked_repos()                   JSON list of every tracked repo
  - show_dashboard()                       returns an HTML resource (Prefab UI)

Run:
  pip install "mcp[cli]" requests
  python github_tracker_server.py            # stdio for MCP clients
  mcp dev github_tracker_server.py           # interactive inspector

Optional: set GITHUB_TOKEN to raise the GitHub API rate limit.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger, configure_logging
from mcp.types import EmbeddedResource, TextResourceContents
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prefab_ui.rx import Rx
from prefab_ui.actions.mcp import CallTool

load_dotenv()

configure_logging(level="INFO")
logger = get_logger("github_tracker")
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Text, Row, Input, Button
from prefab_ui.components.charts import BarChart, ChartSeries

mcp = FastMCP("github-repo-tracker")

DATA_FILE = Path(__file__).parent / "tracked_repos.json"
GITHUB_API = "https://api.github.com/repos/{owner}/{name}"
# GITHUB_API = "https://api.github.com/repos/octocat/Hello-World/issues"


# --- file CRUD helpers ------------------------------------------------------

def _load() -> dict[str, dict[str, Any]]:
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save(data: dict[str, dict[str, Any]]) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _key(owner: str, name: str) -> str:
    return f"{owner}/{name}"


# --- GitHub fetch -----------------------------------------------------------

def _fetch_stats(owner: str, name: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-tracker-mcp",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(
        GITHUB_API.format(owner=owner, name=name), headers=headers, timeout=10
    )
    resp.raise_for_status()
    j = resp.json()
    return {
        "stars": int(j.get("stargazers_count", 0)),
        "forks": int(j.get("forks_count", 0)),
        "open_issues": int(j.get("open_issues_count", 0)),
        "description": j.get("description") or "",
        "html_url": j.get("html_url") or f"https://github.com/{owner}/{name}",
        "language": j.get("language") or "",
    }


# --- tools ------------------------------------------------------------------

@mcp.tool()
def check_github_repo(owner: str, name: str) -> dict:
    """Check if a GitHub repository exists and return its basic details without adding it to the tracker. Use this to verify a repo is valid before adding."""
    try:
        stats = _fetch_stats(owner, name)
        return {"exists": True, "details": stats}
    except Exception as e:
        return {"exists": False, "error": str(e)}


@mcp.tool()
def track_repo(owner: str, name: str, notes: str = "") -> dict:
    """Fetch live GitHub stats for a given repository (owner/name) from the GitHub API and save it to the local tracker JSON file. Use this to start tracking a new repository."""
    logger.info(f"Tool called: track_repo(owner={owner!r}, name={name!r})")
    stats = _fetch_stats(owner, name)
    data = _load()
    k = _key(owner, name)
    data[k] = {
        "owner": owner,
        "name": name,
        "notes": notes,
        "stars": stats.get("stars", 0),
        "forks": stats.get("forks", 0),
        "open_issues": stats.get("open_issues", 0),
        "description": stats.get("description", ""),
        "html_url": stats.get("html_url", ""),
        "language": stats.get("language", ""),
        "last_synced": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save(data)
    return data[k]


@mcp.tool()
def untrack_repo(owner: str, name: str) -> dict:
    """Remove a repository from the local tracker JSON file. Use this when the user wants to stop tracking a repo."""
    logger.info(f"Tool called: untrack_repo(owner={owner!r}, name={name!r})")
    data = _load()
    k = _key(owner, name)
    removed = data.pop(k, None)
    _save(data)
    return {"removed": bool(removed), "repo": k}


@mcp.tool()
def add_custom_repo(owner: str, name: str, stars: int = 0, forks: int = 0, open_issues: int = 0, description: str = "", language: str = "", notes: str = "") -> dict:
    """Manually add a repository entry to the tracker with custom data provided by the user, completely bypassing the GitHub API."""
    logger.info(f"Tool called: add_custom_repo(owner={owner!r}, name={name!r})")
    data = _load()
    k = _key(owner, name)
    data[k] = {
        "owner": owner,
        "name": name,
        "notes": notes,
        "stars": stars,
        "forks": forks,
        "open_issues": open_issues,
        "description": description,
        "html_url": f"https://github.com/{owner}/{name}",
        "language": language,
        "last_synced": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save(data)
    return data[k]


@mcp.tool()
def update_repo_notes(owner: str, name: str, notes: str) -> dict:
    """Update the personal notes field for an already-tracked repository."""
    logger.info(f"Tool called: update_repo_notes(owner={owner!r}, name={name!r})")
    data = _load()
    k = _key(owner, name)
    if k not in data:
        return {"error": f"{k} is not tracked. Call track_repo first."}
    data[k]["notes"] = notes
    _save(data)
    return data[k]


@mcp.tool()
def update_repo_data(owner: str, name: str, stars: int | None = None, forks: int | None = None, open_issues: int | None = None, description: str | None = None, language: str | None = None) -> dict:
    """Manually update specific fields (like stars, forks, issues) of an already-tracked repository without calling the GitHub API."""
    logger.info(f"Tool called: update_repo_data(owner={owner!r}, name={name!r})")
    data = _load()
    k = _key(owner, name)
    if k not in data:
        return {"error": f"{k} is not tracked. Add it first."}
    
    if stars is not None: data[k]["stars"] = stars
    if forks is not None: data[k]["forks"] = forks
    if open_issues is not None: data[k]["open_issues"] = open_issues
    if description is not None: data[k]["description"] = description
    if language is not None: data[k]["language"] = language
    
    data[k]["last_synced"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _save(data)
    return data[k]


@mcp.tool()
def refresh_repo(owner: str, name: str) -> dict:
    """Re-fetch live stats for an already-tracked repository from the GitHub API and update the local tracker."""
    logger.info(f"Tool called: refresh_repo(owner={owner!r}, name={name!r})")
    data = _load()
    k = _key(owner, name)
    if k not in data:
        return {"error": f"{k} is not tracked. Call track_repo first."}
    stats = _fetch_stats(owner, name)
    data[k].update(stats)
    data[k]["last_synced"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _save(data)
    return data[k]


@mcp.tool()
def list_tracked_repos() -> list:
    """Return a list of all repositories currently being tracked in the local JSON file."""
    logger.info("Tool called: list_tracked_repos()")
    return list(_load().values())

def _get_raw_function(func):
    """Extract the original function if wrapped by FastMCP."""
    return getattr(func, "__wrapped__", func)

@mcp.tool(app=True)
def agent_chat(prompt: str) -> PrefabApp:
    """Send a prompt to Gemini LLM to automatically manage the GitHub tracker tools."""
    logger.info(f"Tool called: agent_chat(prompt={prompt!r})")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in .env file. Please create a .env file and add it."
        
    client = genai.Client(api_key=api_key)
    
    tools = [
        _get_raw_function(check_github_repo),
        _get_raw_function(track_repo),
        _get_raw_function(untrack_repo),
        _get_raw_function(add_custom_repo),
        _get_raw_function(update_repo_data),
        _get_raw_function(update_repo_notes),
        _get_raw_function(refresh_repo),
        _get_raw_function(list_tracked_repos),
    ]
    
    try:
        chat = client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                tools=tools,
                temperature=0.1,
            ),
        )
        response = chat.send_message(prompt)
        logger.info(f"Gemini response: {response.text}")
        
        logger.info("--- Chat History ---")
        for idx, message in enumerate(chat.get_history()):
            logger.info(f"[{idx}] Role: {message.role}")
            for part in message.parts:
                if part.text:
                    logger.info(f"   Text: {part.text}")
                elif part.function_call:
                    logger.info(f"   Function Call: {part.function_call.name}({part.function_call.args})")
                elif part.function_response:
                    logger.info(f"   Function Response: {part.function_response.name} -> {part.function_response.response}")
        logger.info("--------------------")

        return show_dashboard(agent_message=response.text)
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        return show_dashboard(agent_message=f"Error executing agent: {e}")


@mcp.tool(app=True)
def show_dashboard(agent_message: str | None = None) -> PrefabApp:
    """Render the dashboard using fastmcp Prefab UI components."""
    logger.info("Tool called: show_dashboard()")
    repos = sorted(_load().values(), key=lambda r: r.get("stars", 0), reverse=True)
    
    with Column(gap=4, css_class="p-6") as view:
        Heading(f"GitHub Repo Tracker ({len(repos)} repos)")
        Text(f"Rendered at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}", css_class="text-sm text-gray-500 mb-4")
        
        with Column(css_class="p-4 border border-gray-700 rounded-lg mb-6"):
            Heading("Ask Gemini Agent", css_class="mb-2 text-lg")
            Text("Enter a prompt to let Gemini automatically add, update, or remove repositories.", css_class="text-sm text-gray-400 mb-2")
            if agent_message:
                Text(agent_message, css_class="text-md text-green-400 font-semibold mb-4 p-2 bg-gray-800 rounded")
            with Row(gap=4):
                Input(name="agent_prompt", placeholder="e.g. Add tiangolo/fastapi to my tracker...")
                Button("Ask Agent", on_click=[
                    CallTool("agent_chat", arguments={"prompt": "{{ agent_prompt }}"})
                ])
                Button("Refresh UI", on_click=[
                    CallTool("show_dashboard")
                ])
        
        if not repos:
            Text("No repos tracked yet. Call track_repo to add one.", css_class="italic text-gray-500")
        else:
            chart_data = [{"repo": f"{r.get('owner')}/{r.get('name')}", "stars": r.get('stars', 0), "forks": r.get('forks', 0)} for r in repos]
            
            with Row(gap=8):
                with Column(gap=4, css_class="flex-1"):
                    Heading("Stars by Repository")
                    BarChart(
                        data=chart_data,
                        series=[ChartSeries(data_key="stars", label="Stars")],
                        x_axis="repo"
                    )
                with Column(gap=4, css_class="flex-1"):
                    Heading("Forks by Repository")
                    BarChart(
                        data=chart_data,
                        series=[ChartSeries(data_key="forks", label="Forks")],
                        x_axis="repo"
                    )

            Heading("Repository Details", css_class="mt-6")
            for r in repos:
                repo_name = f"{r.get('owner')}/{r.get('name')}"
                with Column(css_class="p-4 border rounded-lg mb-2"):
                    Heading(repo_name)
                    Text(f"⭐ Stars: {r.get('stars', 0):,} | 🍴 Forks: {r.get('forks', 0):,} | 🐛 Issues: {r.get('open_issues', 0):,}")
                    if r.get('description'):
                        Text(f"Desc: {r.get('description')}")
                    if r.get('notes') and r.get('notes') != "—":
                        Text(f"Notes: {r.get('notes')}")

    return PrefabApp(view=view)


if __name__ == "__main__":
    mcp.run()
