class DomainException(Exception):
    """Base exception for domain layer."""
    pass

class InvalidArticleError(DomainException):
    """Article validation failed."""
    pass

class EntityExtractionError(DomainException):
    """Entity extraction failed."""
    pass