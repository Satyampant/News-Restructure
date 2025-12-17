import logging
from src.configuration.loader import get_config

def setup_logger(name: str) -> logging.Logger:
    """
    Create configured logger instance.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        A configured logging.Logger instance
    """
    config = get_config()
    
    logger = logging.getLogger(name)
    
    # Set log level (handles string inputs like "INFO" in modern Python)
    logger.setLevel(config.logging.level)
    
    # Avoid adding duplicate handlers if the logger already exists and has handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(config.logging.format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent propagation to root logger to avoid double logging 
        # if the root logger is also configured elsewhere
        logger.propagate = False
    
    return logger