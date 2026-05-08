import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def track_repo(owner: str, name: str, notes: str = "") -> dict:
    """Fetch live GitHub stats."""
    return {}

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

try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='add github repo facebook/react and tiangolo/fastapi',
        config=types.GenerateContentConfig(
            tools=[track_repo, update_repo_data],
            
        ),
    )
    print("Success:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
