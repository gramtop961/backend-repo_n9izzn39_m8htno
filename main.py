import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------
# Helpers
# ----------------------

def serialize_id(value):
    if isinstance(value, ObjectId):
        return str(value)
    return value


def serialize_doc(doc: dict):
    if not doc:
        return doc
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out["id"] = serialize_id(v)
        else:
            out[k] = serialize_id(v)
    return out


# ----------------------
# Pydantic Models
# ----------------------

class ServerIn(BaseModel):
    name: str
    icon_url: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None


class ChannelIn(BaseModel):
    name: str
    type: str = Field("text", pattern="^(text|voice|announcement|stage)$")
    topic: Optional[str] = None
    is_private: bool = False


class MessageIn(BaseModel):
    author_id: str
    author_name: str
    content: str
    attachments: List[str] = []


# ----------------------
# Base endpoints
# ----------------------

@app.get("/")
def read_root():
    return {"message": "Chat API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ----------------------
# Servers
# ----------------------

@app.get("/api/servers")
def list_servers():
    servers = get_documents("server", {})
    return [serialize_doc(s) for s in servers]


@app.post("/api/servers")
def create_server(payload: ServerIn):
    server_id = create_document("server", payload.model_dump())
    doc = db["server"].find_one({"_id": ObjectId(server_id)})
    return serialize_doc(doc)


# ----------------------
# Channels
# ----------------------

@app.get("/api/servers/{server_id}/channels")
def list_channels(server_id: str):
    channels = get_documents("channel", {"server_id": server_id})
    return [serialize_doc(c) for c in channels]


@app.post("/api/servers/{server_id}/channels")
def create_channel(server_id: str, payload: ChannelIn):
    data = payload.model_dump()
    data["server_id"] = server_id
    channel_id = create_document("channel", data)
    doc = db["channel"].find_one({"_id": ObjectId(channel_id)})
    return serialize_doc(doc)


# ----------------------
# Messages
# ----------------------

@app.get("/api/channels/{channel_id}/messages")
def list_messages(channel_id: str, limit: int = 50):
    # Use Mongo for sorting by creation time ascending
    cursor = db["message"].find({"channel_id": channel_id}).sort("created_at", 1).limit(limit)
    return [serialize_doc(m) for m in cursor]


@app.post("/api/channels/{channel_id}/messages")
def send_message(channel_id: str, payload: MessageIn):
    # Basic validation: channel must exist
    channel = db["channel"].find_one({"_id": ObjectId(channel_id)}) if ObjectId.is_valid(channel_id) else db["channel"].find_one({"id": channel_id})
    if not channel:
        # Allow ids passed as plain string stored in server_id, so just continue without strict check
        pass
    data = payload.model_dump()
    data["channel_id"] = channel_id
    msg_id = create_document("message", data)
    doc = db["message"].find_one({"_id": ObjectId(msg_id)})
    return serialize_doc(doc)


# ----------------------
# Seed demo content
# ----------------------

@app.post("/api/seed")
def seed_demo():
    # If servers already exist, return first
    existing = db["server"].find_one()
    if existing:
        server = serialize_doc(existing)
    else:
        server = create_server(ServerIn(name="VibeCord", description="A modern, minimal community"))

    # Ensure a few channels
    server_id = server["id"]
    if db["channel"].count_documents({"server_id": server_id}) == 0:
        for name in ["general", "announcements", "design", "dev-talk"]:
            create_channel(server_id, ChannelIn(name=name, topic=f"Welcome to #{name}"))

    channels = list_channels(server_id)

    # Ensure some messages in first channel
    if channels:
        first_channel = channels[0]
        if db["message"].count_documents({"channel_id": first_channel["id"]}) == 0:
            for text in [
                "Welcome to VibeCord — a clean, modern chat.",
                "Use the message box below to send your first message.",
                "We'll keep things fast and minimal."
            ]:
                send_message(first_channel["id"], MessageIn(author_id="seed", author_name="System", content=text))

    return {
        "server": server,
        "channels": channels,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
