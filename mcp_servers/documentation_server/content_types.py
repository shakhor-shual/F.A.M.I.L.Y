from enum import Enum

class ContentTypes(Enum):
    """Enum defining the different types of content that can be returned by the MCP server"""
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    IMAGE = "image"
    DIAGRAM = "diagram"
    NOTE = "note"
    CATEGORY = "category" 