# Abstract LLM interface
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel

class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass

class LLMProvider(ABC):
    """Abstract base for LLM providers."""
    
    @abstractmethod
    def generate_structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured output matching a Pydantic schema."""
        pass
    
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> str:
        """Generate unstructured text response."""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Test connectivity."""
        pass