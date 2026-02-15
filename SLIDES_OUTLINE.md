# Workshop Slides Outline

## Building Production-Ready AI Agents with Gemini & LangChain
### DevFest Pakistan 2025 - Hamza Ahmad

---

## Slide 1: Title
- **Building Production-Ready AI Agents**
- Gemini & LangChain
- DevFest Pakistan 2025
- Hamza Ahmad, Technical Lead @ Cloudpacer

---

## Slide 2: About Me
- Technical Lead @ Cloudpacer
- Focus: Production AI systems
- Contact: [LinkedIn/GitHub]

---

## Slide 3: Workshop Agenda (60 min)
1. What are AI Agents? (10 min)
2. Building Core Components (20 min)
3. Agent Assembly (20 min)
4. Production Patterns (10 min)

---

## Slide 4: Chatbots vs AI Agents

### Chatbots
- Respond to queries
- Follow scripts
- Limited context

### AI Agents
- **Reason** about tasks
- **Execute** tools
- **Plan** multi-step workflows
- **Adapt** to context

---

## Slide 5: Real-World Agent Example

```
User: "I need a table for 4 tomorrow at 7pm"

Agent Reasoning:
1. Parse request → reservation needed
2. Check requirements → name, phone needed
3. Execute tool → make_reservation()
4. Confirm → provide details
```

---

## Slide 6: Architecture Overview

```
User Message
    ↓
LLM (Gemini)
    ↓
Agent Logic → Decides action
    ↓
Tools → Execute tasks
    ↓
Response
```

---

## Slide 7: Our Restaurant Agent

**Capabilities:**
- Browse menu & dietary options
- Place and track orders
- Make reservations
- Escalate to staff

**Tools:**
- `search_menu`
- `place_order`
- `get_order_status`
- `make_reservation`
- `notify_staff`

---

## Slide 8: Key Concept - Tool Calling

```python
@tool("search_menu")
def search_menu(query: str) -> SearchMenuResult:
    """Search restaurant menu items."""
    # Tool implementation
    return SearchMenuResult(...)
```

**LLM sees:** Function signature + docstring
**LLM decides:** When and how to call

---

## Slide 9: Key Concept - Structured Outputs

```python
class OrderItem(BaseModel):
    menu_item_id: str
    quantity: int = Field(gt=0, le=10)
    special_instructions: str | None

# Automatic validation!
```

Benefits:
- Type safety
- Automatic validation
- Clear contracts
- JSON serialization

---

## Slide 10: Live Demo - Complete Flow

1. Customer asks about menu
2. Agent searches menu
3. Customer places order
4. Agent confirms and tracks
5. Complex issue → escalate

---

## Slide 11: Building Tools (Code)

```python
@tool("place_order")
def place_order(
    customer_name: Annotated[str, Field(...)],
    items: list[dict]
) -> PlaceOrderResult:
    try:
        # Validate inputs
        # Process order
        # Return result
        return PlaceOrderResult(success=True, ...)
    except Exception as e:
        return PlaceOrderResult(success=False, ...)
```

**Key:** Never throw, always return result

---

## Slide 12: Agent Implementation

```python
class RestaurantAgent:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp"
        )
        self.tools = get_restaurant_tools()
        self.agent = create_react_agent(
            llm=self.model,
            tools=self.tools,
            prompt=SYSTEM_PROMPT
        )
```

---

## Slide 13: System Prompt Design

```
YOUR ROLE: Restaurant assistant

WORKFLOWS:
1. MENU BROWSING
   - Use search_menu tool
   - Present results clearly

2. PLACING ORDERS
   - Gather: name, items
   - Use place_order tool
   - Provide confirmation

ESCALATION:
- Use notify_staff for complex issues
```

---

## Slide 14: Production Pattern - Service Layer

```python
@app.post("/api/chat")
async def process_message(request):
    # 1. Validate input
    # 2. Process with agent
    # 3. Handle errors
    # 4. Return structured response
```

FastAPI provides:
- Auto documentation
- Request validation
- Async support

---

## Slide 15: Production Pattern - Error Handling

```python
# Tool level
def tool():
    try:
        # Implementation
        return Result(success=True)
    except Exception as e:
        logger.error(f"Error: {e}")
        return Result(success=False)

# Service level
try:
    result = await agent.process()
except Exception:
    return ErrorResponse(...)
```

---

## Slide 16: Production Pattern - Context Management

```python
from contextvars import ContextVar

_metadata = ContextVar("metadata")

@app.middleware("http")
async def middleware(request, call_next):
    _metadata.set({})  # Initialize
    try:
        return await call_next(request)
    finally:
        _metadata.set(None)  # Cleanup
```

Benefits:
- Request isolation
- Metadata tracking
- Thread-safe

---

## Slide 17: Testing Strategy

```python
def test_search_menu():
    result = search_menu(dietary="vegan")
    assert result.success
    assert all(item.vegan for item in result.items)

def test_invalid_order():
    result = place_order(customer_name="", items=[])
    assert not result.success
    assert "required" in result.message
```

Test:
- Happy paths
- Edge cases
- Error conditions

---

## Slide 18: Hands-On Exercise

**Task:** Add a new tool for recommendations

```python
@tool("get_recommendations")
def get_recommendations(
    preferences: str,
    budget: float
) -> RecommendationResult:
    # TODO: Implement
    pass
```

Consider:
- Input validation
- Filtering logic
- Error handling

---

## Slide 19: Scaling Considerations

**Performance:**
- Cache frequent queries
- Batch operations
- Async processing

**Reliability:**
- Retry logic
- Circuit breakers
- Graceful degradation

**Observability:**
- Structured logging
- Metrics collection
- Distributed tracing

---

## Slide 20: Common Pitfalls

1. **Over-engineering tools**
   - Start simple, iterate

2. **Poor error messages**
   - Be specific and actionable

3. **Ignoring context limits**
   - Manage conversation history

4. **No human escalation**
   - Always have an escape hatch

---

## Slide 21: Best Practices

1. **Type everything** - Use type hints
2. **Validate inputs** - Pydantic models
3. **Handle errors** - Never crash
4. **Log extensively** - Debug in production
5. **Test thoroughly** - Unit + integration
6. **Document tools** - LLM reads docstrings

---

## Slide 22: Advanced Topics

- **Streaming responses** - Better UX
- **Multi-agent systems** - Specialized agents
- **Memory systems** - Long-term context
- **RAG integration** - Knowledge bases
- **Fine-tuning** - Domain-specific models

---

## Slide 23: Resources

**Documentation:**
- LangChain: python.langchain.com
- Gemini: ai.google.dev
- FastAPI: fastapi.tiangolo.com

**Code:**
- Workshop repo: [GitHub link]
- Examples: [Link]

---

## Slide 24: Key Takeaways

1. **Agents > Chatbots** - Reasoning + execution
2. **Tools are interfaces** - Well-designed tools = capable agents
3. **Production needs structure** - Types, validation, error handling
4. **Start simple** - MVP first, iterate
5. **Test everything** - Reliability matters

---

## Slide 25: Q&A

Questions?

**Contact:**
- GitHub: [your-github]
- LinkedIn: [your-linkedin]
- Email: [your-email]

---

## Slide 26: Thank You!

**Next Steps:**
1. Clone the workshop repo
2. Build your own agent
3. Deploy to production
4. Share your experience!

#DevFestPakistan2025