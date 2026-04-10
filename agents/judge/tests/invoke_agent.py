import asyncio
import json
import os
import sys

# Add shared directory to path for imports
sys.path.insert(0, os.path.join(os.getcwd(), "shared"))

from authenticated_httpx import create_authenticated_client


async def test_invoke(url, agent_name, input_text):
    """Invokes the agent via A2A JSON-RPC."""
    # A2A endpoint
    endpoint = f"{url.rstrip('/')}/a2a/{agent_name}"

    # A2A JSON-RPC 2.0 message/send request
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "message/send",
        "params": {
            "message": {
                "messageId": "msg-1",
                "role": "user",
                "parts": [{"text": input_text}],
            }
        },
    }

    print(f"--- Invoking Agent: {agent_name} ---")
    print(f"Endpoint: {endpoint}")
    print(f"Input: {input_text}")
    print("-" * 30)

    try:
        async with create_authenticated_client(endpoint) as client:
            response = await client.post(endpoint, json=payload, timeout=60.0)

            if response.status_code == 200:
                result = response.json()
                print("Response received:")
                print(json.dumps(result, indent=2))

                if "error" in result:
                    print(f"\nResult contains error: {result['error']}")
                elif "result" in result:
                    print("\nSuccess! Result extracted.")
            else:
                print(f"HTTP Error {response.status_code}:")
                print(response.text)
    except Exception as e:
        print(f"Exception during invocation: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python invoke_agent.py <service_url> <agent_name> [input_text]")
        sys.exit(1)

    service_url = sys.argv[1]
    name = sys.argv[2]
    text = (
        sys.argv[3]
        if len(sys.argv) > 3
        else "Python is a versatile programming language."
    )

    asyncio.run(test_invoke(service_url, name, text))
