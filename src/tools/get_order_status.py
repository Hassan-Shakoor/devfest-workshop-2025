from typing import Annotated

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.utils import get_logger

logger = get_logger(__name__)


class OrderStatusResult(BaseModel):
    success: bool
    message: str
    status: str | None = None
    estimated_ready_time: str | None = None
    items_count: int | None = None
    total: float | None = None


@tool("get_order_status")
def get_order_status(
    order_id: Annotated[str, Field(description="Order ID to check status")]
) -> OrderStatusResult:
    """
    Check the status of an existing order.

    Args:
        order_id: The order ID to look up

    Returns:
        OrderStatusResult with current status and details

    Example:
        get_order_status(order_id="ORD-ABC12345")
    """
    try:
        # Import here to avoid circular dependency
        from .place_order import _orders_db

        if not order_id:
            return OrderStatusResult(
                success=False,
                message="Order ID is required"
            )

        # Look up order
        order = _orders_db.get(order_id)

        if not order:
            return OrderStatusResult(
                success=False,
                message=f"Order {order_id} not found"
            )

        # Format status message based on order status
        status_messages = {
            "pending": "Your order is being reviewed",
            "confirmed": "Your order has been confirmed and is being prepared",
            "preparing": "Your order is being prepared in the kitchen",
            "ready": "Your order is ready!",
            "delivered": "Your order has been delivered",
            "cancelled": "Your order has been cancelled"
        }

        message = status_messages.get(
            order.status.value,
            f"Order status: {order.status.value}"
        )

        ready_time = None
        if order.estimated_ready_time:
            ready_time = order.estimated_ready_time.strftime("%I:%M %p")

        return OrderStatusResult(
            success=True,
            message=message,
            status=order.status.value,
            estimated_ready_time=ready_time,
            items_count=len(order.items),
            total=order.total
        )

    except Exception as e:
        logger.error(f"Error checking order status: {e}")
        return OrderStatusResult(
            success=False,
            message=f"Failed to check order status: {str(e)}"
        )