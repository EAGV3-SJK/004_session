import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def track_repo(owner: str, name: str, notes: str = "") -> dict:
    """Fetch live GitHub stats for a given repository (owner/name) from the GitHub API and save it to the local tracker JSON file. Use this to start tracking a new repository."""
    print(f"Executing track_repo({owner}, {name})")
    return {"status": "success", "owner": owner, "name": name}

try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    chat = client.chats.create(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            tools=[track_repo],
            temperature=0.1
        ),
    )
    print("Sending message...")
    response = chat.send_message('add github repo fastapi/fastapi')
    print("Response text:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
