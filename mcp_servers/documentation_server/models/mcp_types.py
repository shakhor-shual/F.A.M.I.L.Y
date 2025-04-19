"""
MCP (Model Context Protocol) Types and Structures

This module defines the core types and structures for the MCP protocol implementation.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import json
import uuid

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder для datetime объектов"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@dataclass
class MCPMessage:
    """Base MCP message structure"""
    id: str
    type: str
    content: Optional[Dict[str, Any]] = None
    error: Optional['MCPError'] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def create(cls, type: str, content: Optional[Dict[str, Any]] = None, error: Optional['MCPError'] = None, metadata: Optional[Dict[str, Any]] = None) -> 'MCPMessage':
        """Create a new MCP message with a generated UUID"""
        return cls(
            id=str(uuid.uuid4()),
            type=type,
            content=content,
            error=error,
            metadata=metadata
        )
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        data = {
            "id": self.id,
            "type": self.type
        }
        if self.content is not None:
            data["content"] = self.content
        if self.error is not None:
            data["error"] = self.error.to_dict()
        if self.metadata is not None:
            data["metadata"] = self.metadata
        return json.dumps(data, cls=DateTimeEncoder)

@dataclass
class MCPAuthentication:
    """MCP authentication structure"""
    token: str
    expires_at: Optional[datetime] = None

class MCPMessageTypes:
    """Standard MCP message types"""
    CONTEXT = "context"
    COMPLETION = "completion"
    FEEDBACK = "feedback"
    ERROR = "error"
    AUTH = "auth"
    DIAGRAM = "diagram"  # Custom type for our diagram operations
    
    # Note-related message types
    CREATE_NOTE = "create_note"
    GET_NOTE = "get_note"
    UPDATE_NOTE = "update_note"
    SEARCH_NOTES = "search_notes"
    LINK_NOTES = "link_notes"
    CREATE_CATEGORY = "create_note_category"
    CREATE_TAG = "create_tag"

class MCPErrorCodes:
    """Standard MCP error codes"""
    INVALID_MESSAGE = "invalid_message"
    AUTHENTICATION_FAILED = "authentication_failed"
    OPERATION_FAILED = "operation_failed"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"

@dataclass
class MCPError:
    """MCP error structure"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details or {}
        } 