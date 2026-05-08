from __future__ import annotations
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_tool(a: int | None = None) -> dict:
    return {}

try:
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    client.chats.create(model='gemini-2.5-flash', config=types.GenerateContentConfig(tools=[test_tool]))
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
