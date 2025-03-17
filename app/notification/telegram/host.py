from app.notification.client import send_telegram_message
from app.models.host import BaseHost
from app.models.admin import Admin
from config import TELEGRAM_LOGGER_TOPIC_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_ADMIN_ID


async def add_host(host: BaseHost, by: Admin):
    data = (
        "*Add Host*\n\n"
        + "➖➖➖➖➖➖➖➖➖"
        + f"**Remark:** {host.remark}\n"
        + f"**Address:** {host.address}\n"
        + f"**Inbound Tag:** {host.inbound_tag}\n"
        + f"**Port:** {host.port}\n\n"
        + "➖➖➖➖➖➖➖➖➖"
        + f"_ID: {host.id}_\n"
        + f"_By: {by.username}_"
    )
    await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def modify_host(host: BaseHost, by: Admin):
    data = (
        "*Modify Host*\n\n"
        + "➖➖➖➖➖➖➖➖➖"
        + f"**Remark:** {host.remark}\n"
        + f"**Address:** {host.address}\n"
        + f"**Inbound Tag:** {host.inbound_tag}\n"
        + f"**Port:** {host.port}\n\n"
        + "➖➖➖➖➖➖➖➖➖"
        + f"_ID: {host.id}_\n"
        + f"_By: {by.username}_"
    )
    await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def remove_host(host: BaseHost, by: Admin):
    data = (
        "*Remove Host*\n\n"
        + "➖➖➖➖➖➖➖➖➖"
        + f"**Remark:** {host.remark}\n"
        + "➖➖➖➖➖➖➖➖➖"
        + f"_ID: {host.id}_\n"
        + f"_By: {by.username}_"
    )
    await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def update_hosts(by: Admin):
    data = "*Add Host*\n\n" + "➖➖➖➖➖➖➖➖➖" + f"All hosts has been updated by **{by.username}**"
    await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)
