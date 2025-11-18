"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# =====================
# Core Chat App Schemas
# =====================

class AppUser(BaseModel):
    """
    Users of the chat application
    Collection name: "appuser"
    """
    username: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    status: Literal["online", "idle", "dnd", "offline"] = "online"
    bio: Optional[str] = None

class Server(BaseModel):
    """
    A server (guild) similar to Discord
    Collection name: "server"
    """
    name: str
    icon_url: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None
    member_ids: List[str] = []

class Channel(BaseModel):
    """
    A channel within a server
    Collection name: "channel"
    """
    server_id: str
    name: str
    type: Literal["text", "voice", "announcement", "stage"] = "text"
    topic: Optional[str] = None
    is_private: bool = False

class Message(BaseModel):
    """
    A message in a channel
    Collection name: "message"
    """
    channel_id: str
    author_id: str
    content: str
    attachments: List[str] = []
    reactions: dict = {}
    is_edited: bool = False

# You can keep the example schemas below if you still need them elsewhere
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
