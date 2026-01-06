import asyncio
import websockets
import json
import sys

async def test_agent_stream():
    uri = "ws://localhost:8000/api/v1/chat/ws/test-session"
    print(f"Connecting to {uri}...")
    sys.stdout.flush()
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            sys.stdout.flush()
            
            # Send message
            msg = {
                "message": "Calculate the 10th Fibonacci number using Python",
                "agent": "python" 
            }
            await websocket.send(json.dumps(msg))
            print(f"Sent: {msg['message']}")
            
            # Listen for responses
            print("Listening for responses...")
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    data = json.loads(response)
                    print(f"Received [{data.get('type')}]: {data.get('content') or data.get('status')}")
                    
                    if data.get("type") in ["response", "error"]:
                        break
                except asyncio.TimeoutError:
                    print("Error: Timeout waiting for response")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_stream())
