#!/usr/bin/env python3
"""
Quick test script to verify the workshop setup works correctly.
Run this after setting up the environment.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from src.models import MenuItem, Order, ConversationContext
        from src.tools import search_menu, place_order
        from src.agents.restaurant_agent import RestaurantAgent
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_tools():
    """Test that tools work."""
    print("\nTesting tools...")
    try:
        from src.tools import search_menu
        from src.models import MenuCategory

        # Test menu search - invoke the tool directly
        result = search_menu.invoke({"category": MenuCategory.MAIN_COURSE})
        assert result.success, "Menu search failed"
        print(f"✓ Menu search works - found {len(result.items)} items")

        # Test order placement
        from src.tools import place_order
        order_result = place_order.invoke({
            "customer_name": "Test User",
            "items": [{"menu_item_id": "main-01", "quantity": 1}]
        })
        assert order_result.success, "Order placement failed"
        print(f"✓ Order placement works - ID: {order_result.order_id}")

        return True
    except Exception as e:
        print(f"✗ Tool test error: {e}")
        return False


async def test_agent():
    """Test that the agent works."""
    print("\nTesting agent...")
    try:
        from src.agents.restaurant_agent import RestaurantAgent
        from src.models import ConversationContext

        agent = RestaurantAgent()
        context = ConversationContext(
            session_id="test-session",
            customer_name="Test User"
        )

        response = await agent.process_message(
            "What vegetarian options do you have?",
            context
        )

        assert response.success, "Agent processing failed"
        print(f"✓ Agent works - Response: {response.response[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Agent test error: {e}")
        return False


def test_api():
    """Test that the API can be imported."""
    print("\nTesting API...")
    try:
        from src.services.restaurant_service import app
        print("✓ API module imports successfully")
        print("  Run 'python src/services/restaurant_service.py' to start the service")
        return True
    except Exception as e:
        print(f"✗ API test error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("DevFest Workshop Test Suite")
    print("=" * 50)

    results = []

    # Test imports
    results.append(test_imports())

    # Test tools
    if results[-1]:  # Only if imports worked
        results.append(test_tools())

    # Test agent (async)
    if all(results):  # Only if previous tests passed
        try:
            import os
            if not os.getenv("GOOGLE_API_KEY"):
                print("\n⚠ Warning: GOOGLE_API_KEY not set in environment")
                print("  Agent test skipped - set your API key in .env file")
            else:
                result = asyncio.run(test_agent())
                results.append(result)
        except Exception as e:
            print(f"\n⚠ Agent test skipped: {e}")

    # Test API
    results.append(test_api())

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n✓ All tests passed! Workshop is ready to go.")
        print("\nNext steps:")
        print("1. Set your GOOGLE_API_KEY in .env file")
        print("2. Run: python src/services/restaurant_service.py")
        print("3. Open: http://localhost:9000/docs")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure virtual environment is activated")
        print("2. Run: pip install -r requirements.txt")
        print("3. Copy .env.example to .env and add your API key")


if __name__ == "__main__":
    main()