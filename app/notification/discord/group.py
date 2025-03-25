from config import DISCORD_WEBHOOK_URL
from app.notification.client import send_discord_webhook
from app.models.group import GroupResponse


async def create_group(group: GroupResponse, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Create Group",
                "description": f"**Name:** {group.name}\n"
                + f"**Inbound Tags:** {group.inbound_tags}\n"
                + f"**Is Disabled:** {group.is_disabled}\n",
                "color": 0x00ff00,
                "footer": {"text": f"ID: {group.id}\nBy: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def modify_group(group: GroupResponse, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Modify Group",
                "description": f"**Name:** {group.name}\n"
                + f"**Inbound Tags:** {group.inbound_tags}\n"
                + f"**Is Disabled:** {group.is_disabled}\n",
                "color": 0xffff00,
                "footer": {"text": f"ID: {group.id}\nBy: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def remove_group(group_id: int, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Remove Group",
                "description": f"**ID:** {group_id}",
                "color": 0xff0000,
                "footer": {"text": f"By: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)
