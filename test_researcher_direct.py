import asyncio
import os

from agents.researcher.agent import researcher
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def main():
    # Ensure API key is available
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not set")
        return

    session_service = InMemorySessionService()
    runner = Runner(
        agent=researcher,
        app_name="test_app",
        session_service=session_service
    )

    session = await session_service.create_session(app_name="test_app", user_id="test_user")
    user_content = types.Content(role="user", parts=[types.Part(text="What are the basics of thermodynamics?")])

    print("Starting researcher...")
    async for event in runner.run_async(user_id="test_user", session_id=session.id, new_message=user_content):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Text: {part.text}")
                if part.executable_code:
                    print(f"Code: {part.executable_code.code}")
                if part.code_execution_result:
                    print(f"Result: {part.code_execution_result.output}")
        if event.actions:
            print(f"Actions: {event.actions}")

if __name__ == "__main__":
    asyncio.run(main())
