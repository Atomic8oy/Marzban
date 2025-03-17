from app.notification.client import send_discord_webhook
from config import DISCORD_WEBHOOK_URL
from app.models.host import BaseHost
from app.models.admin import Admin


async def add_host(host: BaseHost, by: Admin):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Add Host",
                "description": f"**Remark:** {host.remark}\n"
                + f"**Address:** {host.address}\n"
                + f"**Inbound Tag:** {host.inbound_tag}\n"
                + f"**Port:** {host.port}",
                "color": int("00ff00", 16),
                "footer": {"text": f"ID: {host.id}\nBy: {by.username}"},
            }
        ],
    }
    await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def modify_host(host: BaseHost, by: Admin):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Modify Host",
                "description": f"**Remark:** {host.remark}\n"
                + f"**Address:** {host.address}\n"
                + f"**Inbound Tag:** {host.inbound_tag}\n"
                + f"**Port:** {host.port}",
                "color": int("ffff00", 16),
                "footer": {"text": f"ID: {host.id}\nBy: {by.username}"},
            }
        ],
    }
    await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def remove_host(host: BaseHost, by: Admin):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Remove Host",
                "description": f"**Remark:** {host.remark}",
                "color": int("ff0000", 16),
                "footer": {"text": f"ID: {host.id}\nBy: {by.username}"},
            }
        ],
    }
    await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def update_hosts(by: Admin):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Update Hosts",
                "description": f"All hosts has been updated by **{by.username}**",
                "color": int("0000ff", 16),
            }
        ],
    }
    await send_discord_webhook(data, DISCORD_WEBHOOK_URL)
