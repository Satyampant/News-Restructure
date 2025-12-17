from pydantic import BaseModel, Field
from typing import Optional

class ArticleInput(BaseModel):
    """Input model for article ingestion"""
    id: str = Field(..., description="Unique article ID")
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content")
    source: str = Field(..., description="Source name")
    timestamp: str = Field(..., description="ISO format timestamp")
    raw_text: Optional[str] = Field(None, description="Raw article text")