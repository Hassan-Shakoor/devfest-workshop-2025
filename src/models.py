from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class MenuCategory(str, Enum):
    APPETIZER = "appetizer"
    MAIN_COURSE = "main_course"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    SPECIAL = "special"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class MenuItem(BaseModel):
    id: str = Field(description="Unique identifier for menu item")
    name: str = Field(description="Name of the dish")
    description: str = Field(description="Description of the dish")
    price: float = Field(gt=0, description="Price in dollars")
    category: MenuCategory = Field(description="Category of the item")
    available: bool = Field(default=True, description="Whether item is currently available")
    preparation_time_minutes: int = Field(default=20, description="Estimated prep time")
    allergens: list[str] = Field(default_factory=list, description="List of allergens")
    vegetarian: bool = Field(default=False)
    vegan: bool = Field(default=False)
    gluten_free: bool = Field(default=False)

    model_config = ConfigDict(populate_by_name=True)


class OrderItem(BaseModel):
    menu_item_id: str = Field(description="ID of the menu item")
    quantity: int = Field(gt=0, le=10, description="Quantity ordered")
    special_instructions: str | None = Field(default=None, description="Special requests")
    price: float = Field(gt=0, description="Price per item")
    subtotal: float = Field(gt=0, description="Total for this item")

    @field_validator("subtotal", mode="before")
    @classmethod
    def calculate_subtotal(cls, v: Any, info: Any) -> float:
        if v is None and "quantity" in info.data and "price" in info.data:
            return info.data["quantity"] * info.data["price"]
        return v


class Order(BaseModel):
    id: str = Field(description="Unique order identifier")
    customer_name: str = Field(description="Customer's name")
    customer_phone: str | None = Field(default=None, description="Contact phone")
    items: list[OrderItem] = Field(description="Items in the order")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    total: float = Field(gt=0, description="Total order amount")
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_ready_time: datetime | None = Field(default=None)
    delivery_address: str | None = Field(default=None, description="For delivery orders")
    table_number: int | None = Field(default=None, description="For dine-in orders")

    @field_validator("total", mode="before")
    @classmethod
    def calculate_total(cls, v: Any, info: Any) -> float:
        if v is None and "items" in info.data:
            return sum(item.subtotal for item in info.data["items"])
        return v


class Reservation(BaseModel):
    id: str = Field(description="Unique reservation identifier")
    customer_name: str = Field(description="Name for reservation")
    customer_phone: str = Field(description="Contact phone number")
    party_size: int = Field(gt=0, le=12, description="Number of people")
    reservation_date: datetime = Field(description="Date and time of reservation")
    table_number: int | None = Field(default=None, description="Assigned table")
    special_requests: str | None = Field(default=None)
    status: ReservationStatus = Field(default=ReservationStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationContext(BaseModel):
    """Context for agent conversation"""

    session_id: str = Field(description="Unique session identifier")
    customer_name: str | None = Field(default=None)
    current_order_id: str | None = Field(default=None)
    current_reservation_id: str | None = Field(default=None)
    message_count: int = Field(default=0)


class AgentMessage(BaseModel):
    """Message in conversation"""

    role: str = Field(description="Message sender: user or assistant")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessMessageRequest(BaseModel):
    """API request model"""

    message: str = Field(min_length=1, description="User message")
    session_id: str = Field(description="Session identifier")
    context: ConversationContext | None = Field(default=None)
    message_history: list[AgentMessage] = Field(default_factory=list, description="Previous conversation messages")


class ProcessMessageResponse(BaseModel):
    """API response model"""

    success: bool = Field(description="Whether request succeeded")
    response: str | None = Field(default=None, description="Agent response")
    context: ConversationContext | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = Field(default=None)