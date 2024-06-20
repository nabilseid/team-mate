import uvicorn
import socketio
from fastapi import FastAPI
from typing import Dict, List
from weaviate_app import setup_weaviate_interface
from weaviate_app.chat import generic_chat_completions

# Fast API application
app = FastAPI()
# Socket io (sio) create a Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
# wrap with ASGI application
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)

# Dictionary to store session data
sessions: Dict[str, List[Dict[str, str]]] = {}

# Weaviate Interface
# weaviate_interface = setup_weaviate_interface()


# Print {"Hello":"World"} on localhost:7777
@app.get("/")
def read_root():
    return {"Hello": "World"}


@sio.on("connect")
async def connect(sid, env):
    print("New Client Connected to This id :" + " " + str(sid))


@sio.on("disconnect")
async def disconnect(sid):
    print("Client Disconnected: " + " " + str(sid))


@sio.on("connectionInit")
async def handle_connection_init(sid):
    await sio.emit("connectionAck", room=sid)


@sio.on("sessionInit")
async def handle_session_init(sid, data):
    print(f"===> Session {sid} initialized")
    session_id = data.get("sessionId")
    if session_id not in sessions:
        sessions[session_id] = []
    print(f"**** Session {session_id} initialized for {sid} session data: {sessions[session_id]}")
    await sio.emit("sessionInit", {"sessionId": session_id, "chatHistory": sessions[session_id]}, room=sid)


# Handle incoming chat messages
@sio.on("textMessage")
async def handle_chat_message(sid, data):
    print(f"Message from {sid}: {data}")
    session_id = data.get("sessionId")
    if session_id:
        if session_id not in sessions:
            raise Exception(f"Session {session_id} not found")

        received_message = {
            "id": data.get("id"),
            "message": data.get("message"),
            "isUserMessage": True,
            "timestamp": data.get("timestamp"),
        }

        print(data.get("message"))
        job_related, chat_response  = generic_chat_completions(data.get("message"), history=sessions[session_id])
        print('chat_response', chat_response)

        sessions[session_id].append(received_message)

        response_message = {
            "id": data.get("id") + "_response",
            "textResponse": chat_response,
            "jobRelated": job_related,
            "isUserMessage": False,
            "timestamp": data.get("timestamp"),
            "isComplete": True,
        }
        await sio.emit("textResponse", response_message, room=sid)
        sessions[session_id].append(response_message)

        print(f"Message from {sid} in session {session_id}: {data.get('message')}")

    else:
        print(f"No session ID provided by {sid}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6789, lifespan="on", reload=True)
