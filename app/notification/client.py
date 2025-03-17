import httpx

from app.utils.logger import get_logger
from config import TELEGRAM_API_TOKEN


client = httpx.AsyncClient(
    http2=True,
    timeout=httpx.Timeout(10),
    limits=httpx.Limits(max_keepalive_connections=1),
)

logger = get_logger("Notification")


async def send_discord_webhook(json_data, webhook):
    result = await client.post(webhook, json=json_data)

    try:
        result.raise_for_status()
    except httpx.HTTPStatusError | httpx.ConnectError as err:
        logger.error("Discord webhook failed:" + str(err))
    else:
        logger.debug("Discord webhook payload delivered successfully, code {}.".format(result.status_code))


async def send_telegram_message(message, chat_id=None, channel_id=None, topic_id=None):
    """
    Send a message to Telegram based on the available IDs.

    Args:
        message (str): The message to send
        chat_id (str, optional): The chat ID for direct messages
        channel_id (str, optional): The channel ID for channel messages
        topic_id (int, optional): The topic ID for forum topics in channels

    Returns:
        dict: The response from the Telegram API
    """
    base_url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage"

    # Case 1: If topic_id and channel_id are available, send to topic in channel
    if topic_id is not None and channel_id is not None:
        payload = {"chat_id": channel_id, "message_thread_id": topic_id, "parse_mode": "Markdown", "text": message}

    # Case 2: If channel_id is available, send to channel
    elif channel_id is not None:
        payload = {"chat_id": channel_id, "parse_mode": "Markdown", "text": message}

    # Case 3: If only chat_id is available, send to chat
    elif chat_id is not None:
        payload = {"chat_id": chat_id, "parse_mode": "Markdown", "text": message}

    else:
        logger.error("At least one of chat_id, channel_id must be provided")

    # Send the message
    response = await client.post(base_url, data=payload)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError | httpx.ConnectError as err:
        logger.error("Telegram message failed:" + str(err))
    else:
        logger.debug("Telegram message payload delivered successfully, code {}.".format(response.status_code))
