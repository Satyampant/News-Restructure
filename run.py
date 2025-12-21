# Application entry point
import uvicorn
import sys
from pathlib import Path

# Add the project root to sys.path to ensure 'src' module can be found
# This allows running the script directly from the root directory
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from src.configuration.loader import get_config

def main():
    """
    Application Entry Point.
    Loads configuration and starts the Uvicorn server for the FastAPI app.
    """
    # Load the configuration instance
    config = get_config()

    # Log startup details
    print("=" * 50)
    print(f"🚀 Starting {config.api.title}")
    print(f"📦 Version: {config.api.version}")
    print(f"📡 Host: {config.api.host}")
    print(f"🔌 Port: {config.api.port}")
    print(f"🔄 Reload Mode: {'Enabled' if config.api.reload else 'Disabled'}")
    print("=" * 50)

    # Start the Uvicorn server
    # We use the string import format "src.interfaces.rest.app:app" 
    # to ensure that auto-reload works correctly during development.
    uvicorn.run(
        "src.interfaces.rest.app:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_level=config.logging.level.lower(),
        workers=1 if config.api.reload else config.performance.num_workers
    )

if __name__ == "__main__":
    main()