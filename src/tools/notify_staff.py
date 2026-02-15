from typing import Annotated, Literal

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.utils import get_logger
from src.utils.context import get_request_metadata

logger = get_logger(__name__)


class NotifyStaffResult(BaseModel):
    success: bool
    message: str
    ticket_id: str | None = None


@tool("notify_staff")
def notify_staff(
    issue_type: Annotated[
        Literal["complaint", "special_request", "question", "emergency"],
        Field(description="Type of issue requiring staff attention")
    ],
    customer_name: Annotated[str, Field(description="Customer's name")],
    description: Annotated[str, Field(description="Detailed description of the issue")],
    urgency: Annotated[
        Literal["low", "medium", "high"],
        Field(description="Urgency level of the issue")
    ],
    order_id: Annotated[
        str | None,
        Field(description="Related order ID if applicable")
    ] = None,
    table_number: Annotated[
        int | None,
        Field(description="Table number if customer is dining in")
    ] = None,
) -> NotifyStaffResult:
    """
    Notify restaurant staff about an issue requiring human attention.
    This is a TERMINAL tool - using it ends the AI conversation and escalates to staff.

    Args:
        issue_type: Type of issue (complaint, special_request, question, emergency)
        customer_name: Name of the customer
        description: Detailed description of the issue
        urgency: How urgent the issue is (low, medium, high)
        order_id: Related order ID if applicable
        table_number: Table number for dine-in customers

    Returns:
        NotifyStaffResult with ticket information

    Note:
        This tool should be used when:
        - Customer has a complaint that needs human resolution
        - Complex special requests beyond normal ordering
        - Questions the AI cannot answer
        - Emergency situations requiring immediate staff attention
    """
    try:
        # Validate required fields
        if not customer_name or not customer_name.strip():
            return NotifyStaffResult(
                success=False,
                message="Customer name is required for staff notification"
            )

        if not description or not description.strip():
            return NotifyStaffResult(
                success=False,
                message="Issue description is required"
            )

        # Generate ticket ID
        import uuid
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

        # Build notification payload
        notification = {
            "ticket_id": ticket_id,
            "issue_type": issue_type,
            "customer_name": customer_name,
            "description": description,
            "urgency": urgency,
            "order_id": order_id,
            "table_number": table_number
        }

        # Add metadata from request context if available
        try:
            metadata = get_request_metadata()
            session_id = metadata.get("session_id")
            if session_id:
                notification["session_id"] = session_id
        except RuntimeError:
            pass

        # Log the notification (in production, would send to staff system)
        logger.info(f"Staff notification created: {ticket_id}")
        logger.info(f"Issue: {issue_type} - {urgency} urgency")
        logger.info(f"Customer: {customer_name}")
        logger.info(f"Description: {description[:100]}...")

        # Format response message based on urgency
        if urgency == "high" or issue_type == "emergency":
            response_msg = f"I've immediately notified our staff about your {issue_type}. Someone will be with you right away. Ticket: {ticket_id}"
        elif urgency == "medium":
            response_msg = f"I've notified our staff about your {issue_type}. Someone will assist you shortly. Ticket: {ticket_id}"
        else:
            response_msg = f"I've created a ticket for our staff to address your {issue_type}. Ticket: {ticket_id}"

        return NotifyStaffResult(
            success=True,
            message=response_msg,
            ticket_id=ticket_id
        )

    except Exception as e:
        logger.error(f"Error notifying staff: {e}")
        return NotifyStaffResult(
            success=False,
            message=f"Failed to notify staff: {str(e)}",
            ticket_id=None
        )