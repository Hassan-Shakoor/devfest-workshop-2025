import pytest

from src.models import MenuCategory
from src.tools.search_menu import search_menu
from src.tools.place_order import place_order
from src.tools.get_order_status import get_order_status
from src.tools.make_reservation import make_reservation


def test_search_menu_by_category():
    """Test searching menu by category."""
    result = search_menu(category=MenuCategory.APPETIZER)

    assert result.success is True
    assert len(result.items) > 0
    assert all(item.category == MenuCategory.APPETIZER for item in result.items)


def test_search_menu_by_dietary():
    """Test searching menu by dietary restriction."""
    result = search_menu(dietary="vegan")

    assert result.success is True
    if result.items:
        assert all(item.vegan for item in result.items)


def test_search_menu_by_price():
    """Test searching menu by max price."""
    max_price = 15.0
    result = search_menu(max_price=max_price)

    assert result.success is True
    if result.items:
        assert all(item.price <= max_price for item in result.items)


def test_place_order_valid():
    """Test placing a valid order."""
    result = place_order(
        customer_name="Test Customer",
        items=[
            {"menu_item_id": "main-01", "quantity": 2},
            {"menu_item_id": "bev-01", "quantity": 1}
        ],
        table_number=5
    )

    assert result.success is True
    assert result.order_id is not None
    assert result.order_id.startswith("ORD-")
    assert result.total > 0


def test_place_order_invalid_no_name():
    """Test placing order without customer name."""
    result = place_order(
        customer_name="",
        items=[{"menu_item_id": "main-01", "quantity": 1}]
    )

    assert result.success is False
    assert "name is required" in result.message.lower()


def test_place_order_invalid_no_items():
    """Test placing order without items."""
    result = place_order(
        customer_name="Test Customer",
        items=[]
    )

    assert result.success is False
    assert "at least one item" in result.message.lower()


def test_get_order_status_valid():
    """Test getting status of existing order."""
    # First place an order
    order_result = place_order(
        customer_name="Status Test",
        items=[{"menu_item_id": "main-01", "quantity": 1}]
    )

    assert order_result.success is True
    order_id = order_result.order_id

    # Then check its status
    status_result = get_order_status(order_id=order_id)

    assert status_result.success is True
    assert status_result.status is not None
    assert status_result.total > 0


def test_get_order_status_invalid():
    """Test getting status of non-existent order."""
    result = get_order_status(order_id="ORD-NONEXISTENT")

    assert result.success is False
    assert "not found" in result.message.lower()


def test_make_reservation_valid():
    """Test making a valid reservation."""
    result = make_reservation(
        customer_name="Reservation Test",
        customer_phone="555-1234",
        party_size=4,
        reservation_date="2025-12-25 19:00"
    )

    assert result.success is True
    assert result.reservation_id is not None
    assert result.reservation_id.startswith("RES-")
    assert result.table_number is not None


def test_make_reservation_invalid_party_size():
    """Test making reservation with invalid party size."""
    result = make_reservation(
        customer_name="Test",
        customer_phone="555-1234",
        party_size=50,  # Too large
        reservation_date="2025-12-25 19:00"
    )

    assert result.success is False
    assert "party size" in result.message.lower()