import uuid
from datetime import datetime, timedelta
from typing import Annotated

from langchain.tools import tool
from pydantic import BaseModel, Field

from settings import KITCHEN_DELAY_SECONDS, MAX_ORDER_ITEMS
from src.models import Order, OrderItem, OrderStatus
from src.utils import get_logger
from src.utils.context import log_tool_call

logger = get_logger(__name__)

# In-memory order storage
_orders_db: dict[str, Order] = {}


class PlaceOrderResult(BaseModel):
    success: bool
    order_id: str | None = None
    message: str
    total: float | None = None
    estimated_ready_time: str | None = None


@tool("place_order")
def place_order(
    customer_name: Annotated[str, Field(description="Customer's name")],
    items: Annotated[
        list[dict],
        Field(description="List of items with menu_item_id, quantity, and optional special_instructions")
    ],
    customer_phone: Annotated[
        str | None,
        Field(description="Customer phone number for order updates")
    ] = None,
    delivery_address: Annotated[
        str | None,
        Field(description="Delivery address if this is a delivery order")
    ] = None,
    table_number: Annotated[
        int | None,
        Field(description="Table number for dine-in orders")
    ] = None,
) -> PlaceOrderResult:
    """
    Place a new order with the restaurant.

    Args:
        customer_name: Name of the customer
        items: List of order items, each containing:
               - menu_item_id: ID of menu item
               - quantity: Number of items
               - special_instructions: Optional special requests
        customer_phone: Contact phone number
        delivery_address: Address for delivery orders
        table_number: Table for dine-in orders

    Returns:
        PlaceOrderResult with order ID and details

    Example:
        place_order(
            customer_name="John Doe",
            items=[
                {"menu_item_id": "pasta-01", "quantity": 2},
                {"menu_item_id": "salad-02", "quantity": 1, "special_instructions": "No onions"}
            ],
            table_number=5
        )
    """
    try:
        # Validate inputs
        if not customer_name or not customer_name.strip():
            return PlaceOrderResult(
                success=False,
                message="Customer name is required"
            )

        if not items:
            return PlaceOrderResult(
                success=False,
                message="At least one item is required for an order"
            )

        if len(items) > MAX_ORDER_ITEMS:
            return PlaceOrderResult(
                success=False,
                message=f"Maximum {MAX_ORDER_ITEMS} items allowed per order"
            )

        # Create order items
        order_items = []
        total = 0.0

        for item_data in items:
            if "menu_item_id" not in item_data:
                return PlaceOrderResult(
                    success=False,
                    message="Each item must have a menu_item_id"
                )

            quantity = item_data.get("quantity", 1)
            if quantity < 1 or quantity > 10:
                return PlaceOrderResult(
                    success=False,
                    message="Item quantity must be between 1 and 10"
                )

            # Mock price lookup (in real app, would query menu database)
            price = 15.99  # Placeholder price

            order_item = OrderItem(
                menu_item_id=item_data["menu_item_id"],
                quantity=quantity,
                special_instructions=item_data.get("special_instructions"),
                price=price,
                subtotal=price * quantity
            )
            order_items.append(order_item)
            total += order_item.subtotal

        # Create order
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        estimated_ready = datetime.now() + timedelta(seconds=KITCHEN_DELAY_SECONDS)

        order = Order(
            id=order_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            items=order_items,
            status=OrderStatus.CONFIRMED,
            total=total,
            estimated_ready_time=estimated_ready,
            delivery_address=delivery_address,
            table_number=table_number
        )

        # Store order
        _orders_db[order_id] = order

        # Log tool call
        log_tool_call(
            name="place_order",
            arguments={
                "customer_name": customer_name,
                "items": items,
                "table_number": table_number,
                "delivery_address": delivery_address
            },
            result=order_id
        )

        logger.info(f"Order placed: {order_id} for {customer_name}")

        return PlaceOrderResult(
            success=True,
            order_id=order_id,
            message=f"Order confirmed! Your order ID is {order_id}",
            total=total,
            estimated_ready_time=estimated_ready.strftime("%I:%M %p")
        )

    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return PlaceOrderResult(
            success=False,
            message=f"Failed to place order: {str(e)}"
        )