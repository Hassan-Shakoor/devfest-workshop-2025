# Building Production-Ready AI Agents with Gemini & LangChain

DevFest Pakistan 2025 Workshop Materials

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend)
- Google AI API Key (free tier available at https://ai.google.dev/)
- Git and a code editor (VS Code recommended)

### Installation

```bash
# Clone and navigate
cd devfest-workshop-2025

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Run the Backend

```bash
export PYTHONPATH=$PWD:$PYTHONPATH
python src/services/restaurant_service.py
```

The service will start on http://localhost:9000

### Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on http://localhost:5173

### Test the API

```bash
# Health check
curl http://localhost:9000/health

# Chat with the agent
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me your vegetarian options",
    "session_id": "test-session-123"
  }'
```

## Workshop Structure

### Part 1: Understanding AI Agents (10 min)
- Agents vs Chatbots
- Tool calling and structured outputs
- Production architecture patterns

### Part 2: Building the Restaurant Agent (30 min)
- Data models with Pydantic
- Creating tools with LangChain
- Agent implementation with Gemini
- System prompts and workflows

### Part 3: Production Patterns (15 min)
- FastAPI service wrapper
- Request-scoped metadata
- Error handling strategies
- Testing approaches

### Part 4: Hands-on Exercises (5 min)
- Modify the agent prompt
- Add a new tool
- Test edge cases

## Project Structure

```
devfest-workshop-2025/
├── data/
│   └── menu.json               # Restaurant menu data
├── frontend/                   # React frontend (Vite + TailwindCSS)
│   ├── src/
│   │   ├── App.jsx             # Main chat UI component
│   │   ├── main.jsx            # React entry point
│   │   ├── index.css           # Global styles
│   │   └── api/
│   │       └── restaurantClient.js  # API client
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── notebooks/
│   └── building_ai_agents.ipynb  # Interactive workshop notebook
├── src/
│   ├── models.py               # Pydantic data models
│   ├── agents/
│   │   ├── restaurant_agent.py # Main agent logic
│   │   └── prompts.py          # System prompts
│   ├── tools/
│   │   ├── search_menu.py      # Menu search tool
│   │   ├── place_order.py      # Order placement
│   │   ├── get_order_status.py # Order tracking
│   │   ├── make_reservation.py # Table booking
│   │   └── notify_staff.py     # Human escalation
│   ├── services/
│   │   └── restaurant_service.py # FastAPI service
│   └── utils/
│       ├── logger.py           # Logging setup
│       └── context.py          # Request context
├── tests/
│   └── test_tools.py           # Tool unit tests
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── settings.py                 # App configuration
└── test_workshop.py            # Quick setup verification
```

## Key Concepts

### 1. Tool Creation
```python
@tool("search_menu")
def search_menu(query: str) -> SearchMenuResult:
    """Search restaurant menu items."""
    # Implementation
```

### 2. Agent Initialization
```python
agent = RestaurantAgent(
    model_id="gemini-2.0-flash-exp",
    temperature=0.1
)
```

### 3. Processing Messages
```python
response = await agent.process_message(
    message="I want to order pizza",
    context=conversation_context
)
```

## Interactive Notebook

The `notebooks/building_ai_agents.ipynb` notebook provides a step-by-step walkthrough of building the agent, covering data models, tool creation, agent assembly, and production patterns.

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Quick setup verification:
```bash
python test_workshop.py
```

## Common Issues

**Import errors**: Ensure virtual environment is activated
**API key errors**: Check GOOGLE_API_KEY in .env
**Tool execution fails**: Verify all dependencies installed
**Frontend can't connect**: Make sure the backend is running on port 9000

## Resources

- [LangChain Docs](https://python.langchain.com/)
- [Gemini API](https://ai.google.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)

## Workshop Feedback

Please share your feedback at the end of the session!

---

Workshop by Hamza Ahmad, Technical Lead @ Cloudpacer
DevFest Pakistan 2025
