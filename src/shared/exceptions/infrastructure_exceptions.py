class InfrastructureException(Exception):
    """Base exception for infrastructure layer."""
    pass

class DatabaseConnectionError(InfrastructureException):
    """Database connection failed."""
    pass

class LLMServiceError(InfrastructureException):
    """LLM service call failed."""
    pass