import threading
import time
import logging
from bot import run_discord_bot

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def start_bot_in_thread():
    """Start the Discord bot in a separate thread"""
    logger.info("Starting bot in a separate thread")
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.daemon = True
    bot_thread.start()
    logger.info("Bot thread started")
    return bot_thread

# When this module is imported, start the bot
logger.info("Initializing Discord bot")
bot_thread = start_bot_in_thread()