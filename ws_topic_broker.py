import asyncio
import websockets
import json

# Dictionary to store connected clients and their topics
clients = {}

async def handle_client(websocket):
    try:
        # Receive the initial registration message
        message = await websocket.recv()
        reg_data = json.loads(message)
        robot_name = reg_data.get("robot_name")
        publish_topics = reg_data.get("publish_topics", [])
        subscribe_topics = reg_data.get("subscribe_topics", [])

        # Ensure publish_topics and subscribe_topics are lists of hashable types (e.g., strings)
        publish_topics = [str(topic) if isinstance(topic, dict) else topic for topic in publish_topics]
        subscribe_topics = [str(topic) if isinstance(topic, dict) else topic for topic in subscribe_topics]

        # Convert to sets for uniqueness
        publish_topics = set(publish_topics)
        subscribe_topics = set(subscribe_topics)

        if not robot_name:
            print("Client did not provide a robot_name. Closing connection.")
            return
        
        # Store client connection and topics
        clients[websocket] = {
            "robot_name": robot_name,
            "publish_topics": publish_topics,
            "subscribe_topics": subscribe_topics
        }
        
        print(f"[Server] {robot_name} connected. Publishing: {publish_topics}, Subscribing: {subscribe_topics}")
        
        # Keep listening for incoming messages
        async for msg in websocket:
            try:
                data = json.loads(msg)
                topic = data.get("topic")
                message_content = data.get("data")

                print("Message received!")
                
                if topic:
                    # Relay the message to all subscribed clients
                    await distribute_message(topic, message_content, websocket)
            except Exception as e:
                print(f"Error processing message: {e}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {clients[websocket]['robot_name']} disconnected.")
    finally:
        # Remove client from tracking
        if websocket in clients:
            del clients[websocket]


# async def distribute_message(topic, message_content, sender_ws):
#     for client_ws, client_data in clients.items():
#         if topic in client_data["subscribe_topics"] and client_ws != sender_ws:
#             try:
#                 payload = json.dumps({"topic": topic, "data": message_content})
#                 await client_ws.send(payload)
#             except Exception as e:
#                 print(f"Failed to send message to {client_data['robot_name']}: {e}")

async def distribute_message(topic, message_content, sender_ws):
    for client_ws, client_data in clients.items():
        if topic in client_data["subscribe_topics"] and client_ws != sender_ws:
            try:
                payload = json.dumps({"topic": topic, "data": message_content})
                # print(f"Sending to {client_data['robot_name']} on topic '{topic}': {payload}")  # Debugging
                await client_ws.send(payload)
            except Exception as e:
                print(f"Failed to send message to {client_data['robot_name']}: {e}")


async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8080):
        print("WebSocket server started on port 8080...")
        await asyncio.Future()  # Keep server running

if __name__ == "__main__":
    asyncio.run(main())
