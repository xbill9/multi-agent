import asyncio
import os

from google.adk.tools import google_search


async def test_search():
    try:
        print("Testing google_search tool...")
        # google_search is likely a decorated function or an object with a call method
        # In ADK, tools are usually functions.
        result = await google_search("the battle of bosworth fields")
        print(f"Search Result: {result}")
    except Exception as e:
        print(f"Search failed with error: {e}")

if __name__ == "__main__":
    # Ensure API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Warning: GOOGLE_API_KEY not set")
    asyncio.run(test_search())
