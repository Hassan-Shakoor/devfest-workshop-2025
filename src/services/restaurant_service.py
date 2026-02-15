import asyncio
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from settings import SERVICE_HOST, SERVICE_PORT
from src.agents.restaurant_agent import RestaurantAgent
from src.models import ConversationContext, ProcessMessageRequest, ProcessMessageResponse, OrderStatus
from src.utils import get_logger
from src.utils.context import (
    clear_request_metadata,
    get_request_metadata,
    set_request_metadata,
    update_request_metadata,
)

logger = get_logger("RestaurantService")

app = FastAPI(
    title="Restaurant AI Service",
    description="Production-ready restaurant assistant with AI agents",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metadata_middleware(request: Request, call_next) -> Any:
    """
    Initialize and cleanup request-scoped metadata.

    Ensures metadata is:
    1. Initialized at request start
    2. Cleaned up after response
    3. Isolated per request (via contextvars)
    """
    set_request_metadata()

    try:
        response = await call_next(request)
        return response
    finally:
        clear_request_metadata()


# Singleton agent instance
_restaurant_agent: RestaurantAgent | None = None


def get_restaurant_agent() -> RestaurantAgent:
    """Get or create singleton RestaurantAgent instance."""
    global _restaurant_agent
    if _restaurant_agent is None:
        logger.info("Initializing RestaurantAgent...")
        _restaurant_agent = RestaurantAgent()
        logger.info("RestaurantAgent initialized successfully")
    return _restaurant_agent


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "restaurant-ai"
    }


@app.post("/api/chat", response_model=ProcessMessageResponse)
async def process_message(request: ProcessMessageRequest) -> ProcessMessageResponse:
    """
    Process a customer message through the restaurant AI agent.

    This endpoint:
    1. Validates the incoming message
    2. Passes it to the RestaurantAgent
    3. Returns the agent's response with context

    Args:
        request: Message and context from customer

    Returns:
        Agent response with updated context

    Raises:
        HTTPException: For validation errors
    """
    try:
        # Validate request
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )

        logger.info(f"Processing message: {request.message[:100]}...")

        # Update metadata with session info
        update_request_metadata({
            "session_id": request.session_id,
            "timestamp": datetime.now().isoformat()
        })

        # Get or create context
        context = request.context
        if not context:
            context = ConversationContext(
                session_id=request.session_id,
                message_count=0
            )

        # Process with agent
        agent = get_restaurant_agent()
        result = await agent.process_message(
            message=request.message,
            context=context,
            message_history=request.message_history
        )

        # Add metadata to response
        try:
            metadata = get_request_metadata()
            result.metadata.update(metadata)
        except RuntimeError:
            pass

        logger.info(f"Response: {result.response[:100] if result.response else 'None'}...")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return ProcessMessageResponse(
            success=False,
            error=f"Server error: {str(e)}"
        )


@app.post("/api/reset")
async def reset_session(session_id: str) -> dict[str, str]:
    """
    Reset a conversation session.

    Args:
        session_id: Session to reset

    Returns:
        Success message
    """
    logger.info(f"Resetting session: {session_id}")

    # In production, would clear session data from database
    # For workshop, just return success

    return {
        "status": "success",
        "message": f"Session {session_id} reset"
    }


async def update_order_statuses():
    """Background task to update order statuses based on time."""
    from src.tools.place_order import _orders_db

    await asyncio.sleep(10)  # Wait for server to start

    while True:
        try:
            current_time = datetime.now()

            for order_id, order in _orders_db.items():
                # Update status based on elapsed time
                time_since_creation = (current_time - order.created_at).total_seconds()

                if order.status == OrderStatus.CONFIRMED and time_since_creation > 30:
                    order.status = OrderStatus.PREPARING
                    logger.info(f"Order {order_id} now PREPARING")

                elif order.status == OrderStatus.PREPARING and order.estimated_ready_time:
                    if current_time >= order.estimated_ready_time:
                        order.status = OrderStatus.READY
                        logger.info(f"Order {order_id} now READY!")

        except Exception as e:
            logger.error(f"Error updating order statuses: {e}")

        await asyncio.sleep(15)  # Check every 15 seconds


@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup."""
    asyncio.create_task(update_order_statuses())
    logger.info("Background order status updater started")


@app.get("/api/orders/recent")
async def get_recent_orders(session_id: str) -> dict[str, Any]:
    """Get recent orders for a session (for polling)."""
    from src.tools.place_order import _orders_db

    recent_orders = []
    cutoff_time = datetime.now() - timedelta(minutes=30)

    for order_id, order in _orders_db.items():
        if order.created_at >= cutoff_time:
            recent_orders.append({
                "id": order.id,
                "customer_name": order.customer_name,
                "status": order.status.value,
                "total": order.total,
                "estimated_ready_time": order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
                "created_at": order.created_at.isoformat()
            })

    return {"orders": recent_orders}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Restaurant AI Service on {SERVICE_HOST}:{SERVICE_PORT}")

    uvicorn.run(
        app,
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        log_level="info"
    )