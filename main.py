import logging
from keep_alive import app
import bot_runner  # Imported to start the bot automatically

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# For gunicorn to find the app instance
# app is imported from keep_alive

# Log that the app is ready
logger.info("FiveM Discord Bot web interface is ready")

if __name__ == "__main__":
    logger.info("Starting FiveM Discord Bot in development mode")
    # Import and run the full app (this block runs when executing python main.py directly)
    from keep_alive import keep_alive
    
    # Start the web server in a separate thread
    keep_alive()
    
    # Bot is already running from bot_runner import
    # Just keep the main thread alive
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down")
