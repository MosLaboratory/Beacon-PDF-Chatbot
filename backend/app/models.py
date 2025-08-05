"""
Pydantic models for request and response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    """Model for chat request."""
    message: str = Field(..., description="User message", min_length=1, max_length=2000)
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None, 
        description="Previous conversation messages"
    )

class ChatResponse(BaseModel):
    """Model for chat response."""
    response: str = Field(..., description="AI response")
    conversation_history: List[ChatMessage] = Field(..., description="Updated conversation history")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")

class UploadResponse(BaseModel):
    """Model for PDF upload response."""
    filename: str = Field(..., description="Name of the uploaded file")
    pages: int = Field(..., description="Number of pages in the PDF")
    text_length: int = Field(..., description="Length of extracted text")
    message: str = Field(..., description="Success message")

class HealthResponse(BaseModel):
    """Model for health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0", description="API version")

class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now) 