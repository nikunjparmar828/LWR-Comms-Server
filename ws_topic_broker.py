import asyncio
import websockets
import json

# Dictionary to store connected clients and their topics
clients = {}

def extract_topic_list(topic_list):
    topics = []
    for topic in topic_list:
        if isinstance(topic, dict):
            topics.append(topic.get("name", ""))
        else:
            topics.append(str(topic))
    return set(topics)

async def handle_client(websocket):
    try:
        # Receive the initial registration message
        message = await websocket.recv()
        reg_data = json.loads(message)
        robot_name = reg_data.get("robot_name")
        publish_topics = extract_topic_list(reg_data.get("publish_topics", []))
        subscribe_topics = extract_topic_list(reg_data.get("subscribe_topics", []))

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

        # Listen for incoming messages
        async for msg in websocket:
            try:
                data = json.loads(msg)
                topic = data.get("topic")
                message_content = data.get("data")
                if topic:
                    # Prepend the sender's robot name to the topic if not already present
                    sender_robot = clients[websocket]["robot_name"]
                    if not topic.startswith(f"/{sender_robot}"):
                        modified_topic = f"/{sender_robot}{topic}"
                    else:
                        modified_topic = topic
                    print(f"[Server] Forwarding message on topic: {modified_topic}")
                    await distribute_message(modified_topic, message_content, websocket)
            except Exception as e:
                print(f"Error processing message: {e}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {clients[websocket]['robot_name']} disconnected.")
    finally:
        if websocket in clients:
            del clients[websocket]

# IMP information about the frame_data:
async def distribute_message(topic, message_content, sender_ws):
    # print("Message content to forward:", message_content)
    for client_ws, client_data in clients.items():
        # print(client_ws)
        # print("--------------")
        # print(client_data)
        # Forward if the subscribing client has registered for the modified topic and is not the sender
        if topic in client_data["subscribe_topics"]:
            print("This is working!!!")
            # print("Forwarding to", client_data["robot_name"])
            try:
                payload = json.dumps({"topic": topic, "data": message_content})
                print("Message content to forward:", message_content)
                await client_ws.send(payload)
            except Exception as e:
                print(f"Failed to send message to {client_data['robot_name']}: {e}")

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8080):
        print("WebSocket server started on port 8080...")
        await asyncio.Future()  # Keep server running

if __name__ == "__main__":
    asyncio.run(main())
