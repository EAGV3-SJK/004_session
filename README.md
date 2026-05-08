# GitHub Repo Tracker (FastMCP + Prefab UI + Gemini)

An interactive, agent-powered GitHub repository tracker built using the Model Context Protocol (**FastMCP**), **Prefab UI**, and **Google Gemini 2.5 Flash**.

This application provides a rich local dashboard to monitor your favorite GitHub repositories. It features an integrated AI agent that can automatically track, untrack, and update repository data using natural language prompts, complete with seamless, real-time UI updates.

## Features

- **📊 Prefab UI Dashboard**: A responsive, reactive dashboard built purely in Python that visualizes your tracked repositories, displaying live stars, forks, and issues.
- **🤖 Gemini Agent Integration**: Simply type `"Add the django/django repo to my tracker"` and Gemini will automatically execute the necessary backend tools (API lookups, database additions) and refresh your UI.
- **🔄 Automated Function Calling**: Leverages the `google-genai` SDK's Automatic Function Calling (AFC) to handle multi-step reasoning and tool execution under the hood.
- **💾 Local Persistence**: All repository data is persistently stored in a local `tracked_repos.json` file.
- **⚡ Live GitHub API Fetching**: Automatically pulls live metrics directly from the GitHub API.

## Requirements

- Python 3.10+
- A Google Gemini API Key
- *(Optional)* A GitHub Personal Access Token (PAT)

## Installation

1. **Clone or navigate to the project directory.**
2. **Install the required dependencies:**
   ```bash
   pip install "mcp[cli]" requests google-genai python-dotenv prefab-ui
   ```
3. **Configure Environment Variables:**
   Create a `.env` file in the root of the project directory and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Optional: Add a GitHub token to increase your rate limit from 60 to 5000 requests/hour
   GITHUB_TOKEN=ghp_your_github_token_here
   ```

## Running the Application

This project utilizes `fastmcp dev` to serve both the MCP server and the interactive Prefab UI dashboard.

Start the server by running:
```bash
fastmcp dev apps github_tracker_server.py
```

Once started, open your browser and navigate to:
**http://localhost:8080**

## How to Use the Agent

1. Open the dashboard in your browser.
2. Locate the **"Ask Gemini Agent"** section at the top.
3. Enter natural language prompts. Examples:
   - *"Can you add the tiangolo/fastapi repository to my tracker?"*
   - *"Remove facebook/react from the tracker."*
   - *"Update the notes for django/django to say 'Backend framework'"*
4. Click **Ask Agent**.
5. The terminal will log the exact underlying `Chat History` (showing the function calls and responses). Once complete, the dashboard will automatically refresh to show your new data, alongside a direct response message from Gemini!

## Architecture

- **`github_tracker_server.py`**: The core FastMCP server. It defines all the standard tools (`track_repo`, `untrack_repo`, etc.), the `show_dashboard` UI tool, and the `agent_chat` tool.
- **`tracked_repos.json`**: The local JSON database where repository metrics and metadata are stored.
- **Tool Chaining**: The `agent_chat` tool accepts user input, initializes a Gemini chat session with access to all other MCP tools, and returns a fully re-rendered `PrefabApp` view upon success to seamlessly update the frontend.
