import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from github_tracker_server import *
from github_tracker_server import _get_raw_function
import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

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
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    chat = client.chats.create(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            tools=tools,
            temperature=0.1
        ),
    )
    print("Sending message...")
    response = chat.send_message('add github repo fastapi/fastapi')
    print("Response text:", response.text)
    for message in chat.get_history():
        print(message)
except Exception as e:
    import traceback
    traceback.print_exc()
