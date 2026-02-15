import uuid
from datetime import datetime
from typing import Annotated

from langchain.tools import tool
from pydantic import BaseModel, Field

from settings import MAX_PARTY_SIZE
from src.models import Reservation, ReservationStatus
from src.utils import get_logger

logger = get_logger(__name__)

# In-memory reservation storage
_reservations_db: dict[str, Reservation] = {}


class ReservationResult(BaseModel):
    success: bool
    reservation_id: str | None = None
    message: str
    table_number: int | None = None


@tool("make_reservation")
def make_reservation(
    customer_name: Annotated[str, Field(description="Name for the reservation")],
    customer_phone: Annotated[str, Field(description="Contact phone number")],
    party_size: Annotated[int, Field(description="Number of people (1-12)")],
    reservation_date: Annotated[str, Field(description="Date and time (ISO format or natural language)")],
    special_requests: Annotated[
        str | None,
        Field(description="Special requests or notes")
    ] = None,
) -> ReservationResult:
    """
    Make a table reservation at the restaurant.

    Args:
        customer_name: Name for the reservation
        customer_phone: Contact phone number
        party_size: Number of people in the party
        reservation_date: Desired date and time
        special_requests: Any special requests

    Returns:
        ReservationResult with reservation details

    Example:
        make_reservation(
            customer_name="Jane Smith",
            customer_phone="555-1234",
            party_size=4,
            reservation_date="2024-12-07 19:30"
        )
    """
    try:
        # Validate inputs
        if not customer_name or not customer_name.strip():
            return ReservationResult(
                success=False,
                message="Customer name is required"
            )

        if not customer_phone:
            return ReservationResult(
                success=False,
                message="Phone number is required for reservations"
            )

        if party_size < 1 or party_size > MAX_PARTY_SIZE:
            return ReservationResult(
                success=False,
                message=f"Party size must be between 1 and {MAX_PARTY_SIZE}"
            )

        # Parse reservation date
        try:
            if isinstance(reservation_date, str):
                # Simple ISO format parsing
                res_datetime = datetime.fromisoformat(reservation_date.replace("Z", "+00:00"))
            else:
                res_datetime = reservation_date
        except Exception:
            # Fallback to current time + 2 hours for demo
            res_datetime = datetime.now().replace(hour=19, minute=0)

        # Check if reservation is in the past
        if res_datetime < datetime.now():
            return ReservationResult(
                success=False,
                message="Cannot make reservations for past dates"
            )

        # Generate reservation ID
        reservation_id = f"RES-{uuid.uuid4().hex[:8].upper()}"

        # Mock table assignment (in real app, would check availability)
        table_number = (party_size % 10) + 1

        # Create reservation
        reservation = Reservation(
            id=reservation_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            party_size=party_size,
            reservation_date=res_datetime,
            table_number=table_number,
            special_requests=special_requests,
            status=ReservationStatus.CONFIRMED
        )

        # Store reservation
        _reservations_db[reservation_id] = reservation

        logger.info(f"Reservation created: {reservation_id} for {customer_name}")

        return ReservationResult(
            success=True,
            reservation_id=reservation_id,
            message=f"Reservation confirmed for {party_size} people on {res_datetime.strftime('%B %d at %I:%M %p')}",
            table_number=table_number
        )

    except Exception as e:
        logger.error(f"Error making reservation: {e}")
        return ReservationResult(
            success=False,
            message=f"Failed to make reservation: {str(e)}"
        )