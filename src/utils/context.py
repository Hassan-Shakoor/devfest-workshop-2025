from contextvars import ContextVar
from typing import Any

_request_metadata: ContextVar[dict[str, Any] | None] = ContextVar(
    "request_metadata", default=None
)


def set_request_metadata(metadata: dict[str, Any] | None = None) -> None:
    """Initialize metadata for the current request context."""
    _request_metadata.set(metadata or {})


def get_request_metadata() -> dict[str, Any]:
    """Get current request metadata."""
    metadata = _request_metadata.get()
    if metadata is None:
        raise RuntimeError("Request metadata not initialized")
    return metadata


def update_request_metadata(updates: dict[str, Any]) -> None:
    """Update request metadata with new values."""
    metadata = get_request_metadata()
    metadata.update(updates)


def clear_request_metadata() -> None:
    """Clear request metadata."""
    _request_metadata.set(None)


def log_tool_call(name: str, arguments: dict[str, Any], result: Any) -> None:
    """Log a tool call to request metadata."""
    try:
        metadata = get_request_metadata()
        if "tool_calls" not in metadata:
            metadata["tool_calls"] = []
        metadata["tool_calls"].append({
            "name": name,
            "arguments": arguments,
            "result": str(result) if result else None
        })
    except RuntimeError:
        pass