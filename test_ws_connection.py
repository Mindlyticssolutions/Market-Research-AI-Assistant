
import asyncio
import websockets
import json
import uuid

async def test_websocket():
    session_id = str(uuid.uuid4())
    uri = f"ws://127.0.0.1:8000/api/v1/chat/ws/{session_id}"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Sending message...")
            await websocket.send(json.dumps({
                "message": "ping",
                "agent": "orchestrator"
            }))
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    print(f"Received: {data}")
                    if data.get("type") == "response" or data.get("type") == "error":
                        break
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
    except Exception as e:
        print(f"WS Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
