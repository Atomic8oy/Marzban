from app.notification.client import send_telegram_message
from app.models.node import NodeResponse
from config import TELEGRAM_LOGGER_TOPIC_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_ADMIN_ID, TELEGRAM_NOTIFY


async def create_node(node: NodeResponse, by: str):
    data = (
        "*#Create_Node*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**ID:** `{node.id}`\n"
        + f"**Name:** `{node.name}`\n"
        + f"**Address:** `{node.address}`\n"
        + f"**Port:** `{node.port}`\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"_By: #{by}_"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def modify_node(node: NodeResponse, by: str):
    data = (
        "*#Modify_Node*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**ID:** `{node.id}`\n"
        + f"**Name:** `{node.name}`\n"
        + f"**Address:** `{node.address}`\n"
        + f"**Port:** `{node.port}`\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"_By: #{by}_"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def remove_node(node: NodeResponse, by: str):
    data = (
        "*#Remove_Node*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**ID:** `{node.id}`\n"
        + f"**Name:** `{node.name}`\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"_By: #{by}_"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def connect_node(node: NodeResponse):
    data = (
        "*#Connect_Node*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**Name:** `{node.name}`\n"
        + f"**Node Version:** {node.node_version}\n"
        + f"**Core Version:** {node.xray_version}\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"_ID_: `{node.id}`"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def error_node(node: NodeResponse):
    data = (
        "*#Error_Node*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**Name:** `{node.name}`\n"
        + f"**Error:** {node.message}\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"_ID_: `{node.id}`"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)
