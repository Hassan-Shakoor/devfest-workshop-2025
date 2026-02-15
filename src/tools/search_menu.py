import json
from pathlib import Path
from typing import Annotated

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.models import MenuCategory, MenuItem
from src.utils import get_logger

logger = get_logger(__name__)


class SearchMenuResult(BaseModel):
    success: bool
    items: list[MenuItem] = Field(default_factory=list)
    message: str
    total_results: int = 0


def load_menu_data() -> list[MenuItem]:
    """Load menu data from JSON file."""
    menu_file = Path(__file__).parent.parent.parent / "data" / "menu.json"

    if not menu_file.exists():
        logger.warning(f"Menu file not found at {menu_file}")
        return []

    try:
        with open(menu_file, "r") as f:
            data = json.load(f)
            return [MenuItem(**item) for item in data.get("items", [])]
    except Exception as e:
        logger.error(f"Error loading menu data: {e}")
        return []


@tool("search_menu")
def search_menu(
    query: Annotated[
        str | None,
        Field(description="Search query for menu items (searches name and description)")
    ] = None,
    category: Annotated[
        MenuCategory | None,
        Field(description="Filter by category (appetizer, main_course, dessert, beverage)")
    ] = None,
    max_price: Annotated[
        float | None,
        Field(description="Maximum price filter")
    ] = None,
    dietary: Annotated[
        str | None,
        Field(description="Dietary filter: vegetarian, vegan, gluten_free")
    ] = None,
) -> SearchMenuResult:
    """
    Search restaurant menu items with various filters.

    Args:
        query: Text search in item names and descriptions
        category: Filter by menu category
        max_price: Maximum price limit
        dietary: Dietary restriction filter

    Returns:
        SearchMenuResult with matching menu items

    Examples:
        - search_menu(query="pasta") - Find all pasta dishes
        - search_menu(category="appetizer") - All appetizers
        - search_menu(dietary="vegan") - All vegan options
        - search_menu(max_price=15.0) - Items under $15
    """
    try:
        menu_items = load_menu_data()

        if not menu_items:
            return SearchMenuResult(
                success=False,
                message="Menu data not available",
                items=[]
            )

        filtered_items = menu_items

        # Apply query filter
        if query:
            query_lower = query.lower()
            filtered_items = [
                item for item in filtered_items
                if query_lower in item.name.lower() or
                   query_lower in item.description.lower()
            ]

        # Apply category filter
        if category:
            filtered_items = [
                item for item in filtered_items
                if item.category == category
            ]

        # Apply price filter
        if max_price is not None:
            filtered_items = [
                item for item in filtered_items
                if item.price <= max_price
            ]

        # Apply dietary filter
        if dietary:
            dietary_lower = dietary.lower()
            if dietary_lower == "vegetarian":
                filtered_items = [item for item in filtered_items if item.vegetarian]
            elif dietary_lower == "vegan":
                filtered_items = [item for item in filtered_items if item.vegan]
            elif dietary_lower == "gluten_free":
                filtered_items = [item for item in filtered_items if item.gluten_free]

        # Only show available items
        filtered_items = [item for item in filtered_items if item.available]

        if not filtered_items:
            return SearchMenuResult(
                success=True,
                items=[],
                message="No items found matching your criteria",
                total_results=0
            )

        return SearchMenuResult(
            success=True,
            items=filtered_items[:10],  # Limit to 10 results
            message=f"Found {len(filtered_items)} menu items",
            total_results=len(filtered_items)
        )

    except Exception as e:
        logger.error(f"Error searching menu: {e}")
        return SearchMenuResult(
            success=False,
            items=[],
            message=f"Error searching menu: {str(e)}",
            total_results=0
        )