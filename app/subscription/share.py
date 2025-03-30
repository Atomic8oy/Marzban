import base64
import random
import secrets
from collections import defaultdict
from copy import deepcopy
from datetime import timezone, timedelta, datetime as dt
from jdatetime import date as jd

from app import backend
from app.db.models import User, UserStatus
from app.utils.system import get_public_ip, get_public_ipv6, readable_size

from . import (
    StandardLinks,
    XrayConfig,
    SingBoxConfiguration,
    ClashConfiguration,
    ClashMetaConfiguration,
    OutlineConfiguration,
)

from config import (
    ACTIVE_STATUS_TEXT,
    DISABLED_STATUS_TEXT,
    EXPIRED_STATUS_TEXT,
    HOST_STATUS_FILTER,
    LIMITED_STATUS_TEXT,
    ONHOLD_STATUS_TEXT,
    REMOVE_HOSTS_WITH_NO_STATUS,
)

SERVER_IP = get_public_ip()
SERVER_IPV6 = get_public_ipv6()

STATUS_EMOJIS = {
    "active": "✅",
    "expired": "⌛️",
    "limited": "🪫",
    "disabled": "❌",
    "on_hold": "🔌",
}

STATUS_TEXTS = {
    "active": ACTIVE_STATUS_TEXT,
    "expired": EXPIRED_STATUS_TEXT,
    "limited": LIMITED_STATUS_TEXT,
    "disabled": DISABLED_STATUS_TEXT,
    "on_hold": ONHOLD_STATUS_TEXT,
}


async def generate_standard_links(
    proxies: dict, inbounds: list[str], extra_data: dict, reverse: bool, user_status: UserStatus
) -> list:
    format_variables = setup_format_variables(extra_data)
    conf = StandardLinks()
    return await process_inbounds_and_tags(
        inbounds, proxies, format_variables, conf=conf, reverse=reverse, user_status=user_status
    )


async def generate_clash_subscription(
    proxies: dict,
    inbounds: list[str],
    extra_data: dict,
    reverse: bool,
    is_meta: bool = False,
    user_status: UserStatus = UserStatus.active,
) -> str:
    if is_meta is True:
        conf = ClashMetaConfiguration()
    else:
        conf = ClashConfiguration()

    format_variables = setup_format_variables(extra_data)
    return await process_inbounds_and_tags(
        inbounds, proxies, format_variables, conf=conf, reverse=reverse, user_status=user_status
    )


async def generate_singbox_subscription(
    proxies: dict, inbounds: list[str], extra_data: dict, reverse: bool, user_status: UserStatus
) -> str:
    conf = SingBoxConfiguration()

    format_variables = setup_format_variables(extra_data)
    return await process_inbounds_and_tags(inbounds, proxies, format_variables, conf=conf, reverse=reverse)


async def generate_outline_subscription(
    proxies: dict, inbounds: list[str], extra_data: dict, reverse: bool, user_status: UserStatus
) -> str:
    conf = OutlineConfiguration()

    format_variables = setup_format_variables(extra_data)
    return await process_inbounds_and_tags(
        inbounds, proxies, format_variables, conf=conf, reverse=reverse, user_status=user_status
    )


async def generate_xray_subscription(
    proxies: dict, inbounds: list[str], extra_data: dict, reverse: bool, user_status: UserStatus
) -> str:
    conf = XrayConfig()

    format_variables = setup_format_variables(extra_data)
    return await process_inbounds_and_tags(
        inbounds, proxies, format_variables, conf=conf, reverse=reverse, user_status=user_status
    )


async def generate_subscription(user: User, config_format: str, as_base64: bool, reverse: bool = False) -> str:
    kwargs = {
        "proxies": user.proxy_settings,
        "user_status": user.status,
        "inbounds": user.inbounds(backend.config.inbounds),
        "extra_data": user.__dict__,
        "reverse": reverse,
    }

    if config_format == "links":
        config = "\n".join(generate_standard_links(**kwargs))
    elif config_format == "clash-meta":
        config = generate_clash_subscription(**kwargs, is_meta=True)
    elif config_format == "clash":
        config = generate_clash_subscription(**kwargs)
    elif config_format == "sing-box":
        config = generate_singbox_subscription(**kwargs)
    elif config_format == "outline":
        config = generate_outline_subscription(**kwargs)
    elif config_format == "xray":
        config = generate_xray_subscription(**kwargs)
    else:
        raise ValueError(f'Unsupported format "{config_format}"')

    if as_base64:
        config = base64.b64encode(config.encode()).decode()

    return config


def format_time_left(seconds_left: int) -> str:
    if not seconds_left or seconds_left <= 0:
        return "∞"

    minutes, seconds = divmod(seconds_left, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    months, days = divmod(days, 30)

    result = []
    if months:
        result.append(f"{months}m")
    if days:
        result.append(f"{days}d")
    if hours and (days < 7):
        result.append(f"{hours}h")
    if minutes and not (months or days):
        result.append(f"{minutes}m")
    if seconds and not (months or days):
        result.append(f"{seconds}s")
    return " ".join(result)


def setup_format_variables(extra_data: dict) -> dict:
    user_status = extra_data.get("status")
    expire = extra_data.get("expire")
    on_hold_expire_duration = extra_data.get("on_hold_expire_duration")
    now = dt.now(timezone.utc)

    if user_status != UserStatus.on_hold:
        if expire is not None:
            seconds_left = (expire - now).total_seconds()
            expire_date = expire.date()
            jalali_expire_date = jd.fromgregorian(
                year=expire_date.year, month=expire_date.month, day=expire_date.day
            ).strftime("%Y-%m-%d")
            if now < expire:
                days_left = (expire - dt.utcnow()).days + 1
                time_left = format_time_left(seconds_left)
            else:
                days_left = "0"
                time_left = "0"

        else:
            days_left = "∞"
            time_left = "∞"
            expire_date = "∞"
            jalali_expire_date = "∞"
    else:
        if on_hold_expire_duration:
            days_left = timedelta(seconds=on_hold_expire_duration).days
            time_left = format_time_left(on_hold_expire_duration)
            expire_date = "-"
            jalali_expire_date = "-"
        else:
            days_left = "∞"
            time_left = "∞"
            expire_date = "∞"
            jalali_expire_date = "∞"

    if extra_data.get("data_limit"):
        data_limit = readable_size(extra_data["data_limit"])
        data_left = extra_data["data_limit"] - extra_data["used_traffic"]
        usage_Percentage = round((extra_data["used_traffic"] / extra_data["data_limit"]) * 100.0, 2)

        if data_left < 0:
            data_left = 0
        data_left = readable_size(data_left)
    else:
        data_limit = "∞"
        data_left = "∞"
        usage_Percentage = "∞"

    status_emoji = STATUS_EMOJIS.get(extra_data.get("status")) or ""
    status_template = STATUS_TEXTS.get(extra_data.get("status")) or ""

    # Create a temporary dictionary with variables excluding STATUS_TEXT
    temp_vars = {
        "SERVER_IP": SERVER_IP,
        "SERVER_IPV6": SERVER_IPV6,
        "USERNAME": extra_data.get("username", "{USERNAME}"),
        "DATA_USAGE": readable_size(extra_data.get("used_traffic")),
        "DATA_LIMIT": data_limit,
        "DATA_LEFT": data_left,
        "DAYS_LEFT": days_left,
        "EXPIRE_DATE": expire_date,
        "JALALI_EXPIRE_DATE": jalali_expire_date,
        "TIME_LEFT": time_left,
        "STATUS_EMOJI": status_emoji,
        "USAGE_PERCENTAGE": usage_Percentage,
    }

    # Format the status text using the temporary variables
    status_text = status_template.format_map(defaultdict(lambda: "<missing>", temp_vars))

    # Create the final format_variables including the formatted STATUS_TEXT
    format_variables = defaultdict(
        lambda: "<missing>",
        {
            **temp_vars,
            "STATUS_TEXT": status_text,
        },
    )

    return format_variables


def filter_hosts(hosts: list, user_status: UserStatus) -> list:
    if not HOST_STATUS_FILTER:
        return hosts

    if user_status in (UserStatus.active, UserStatus.on_hold):
        return [host for host in hosts if not host["status"] or user_status in host["status"]]

    if REMOVE_HOSTS_WITH_NO_STATUS:
        return [host for host in hosts if host["status"] and user_status in host["status"]]

    return [host for host in hosts if not host["status"] or user_status in host["status"]]


async def process_inbounds_and_tags(
    inbounds: list[str],
    proxies: dict,
    format_variables: dict,
    conf: StandardLinks
    | XrayConfig
    | SingBoxConfiguration
    | ClashConfiguration
    | ClashMetaConfiguration
    | OutlineConfiguration,
    reverse=False,
    user_status: UserStatus = UserStatus.active,
) -> list | str:
    for host in filter_hosts(backend.hosts.values(), user_status):
        tag = host["inbound_tag"]
        host_inbound = deepcopy(backend.config.inbounds_by_tag[tag])

        protocol = host_inbound["protocol"]

        if tag not in inbounds:
            continue

        settings = proxies.get(protocol)
        if not settings:
            continue

        format_variables.update({"PROTOCOL": protocol})
        format_variables.update({"TRANSPORT": host_inbound["network"]})
        sni = ""
        sni_list = host["sni"] or host_inbound["sni"]
        if sni_list:
            salt = secrets.token_hex(8)
            sni = random.choice(sni_list).replace("*", salt)

        req_host = ""
        req_host_list = host["host"] or host_inbound["host"]
        if req_host_list:
            salt = secrets.token_hex(8)
            req_host = random.choice(req_host_list).replace("*", salt)

        address = ""
        address_list = host["address"]
        if host["address"]:
            salt = secrets.token_hex(8)
            address = random.choice(address_list).replace("*", salt)

        if sids := host_inbound.get("sids"):
            host_inbound["sid"] = random.choice(sids)

        if host["path"] is not None:
            path = host["path"].format_map(format_variables)
        else:
            path = host_inbound.get("path", "").format_map(format_variables)

        if host.get("use_sni_as_host", False) and sni:
            req_host = sni

        host_inbound.update(
            {
                "port": host["port"] or host_inbound["port"],
                "sni": sni,
                "host": req_host,
                "tls": host_inbound["tls"] if host["tls"] is None else host["tls"],
                "alpn": host["alpn"] if host["alpn"] else None,
                "path": path,
                "fp": host["fingerprint"] or host_inbound.get("fp", ""),
                "ais": host["allowinsecure"] or host_inbound.get("allowinsecure", ""),
                "fragment_settings": host["fragment_settings"],
                "noise_settings": host["noise_settings"],
                "random_user_agent": host["random_user_agent"],
                "http_headers": host["http_headers"],
                "mux_settings": host["mux_settings"],
            }
        )
        if ts := host["transport_settings"]:
            for v in ts.values():
                if v:
                    host_inbound.update(v)

        conf.add(
            remark=host["remark"].format_map(format_variables),
            address=address.format_map(format_variables),
            inbound=host_inbound,
            settings=settings,
        )

    return conf.render(reverse=reverse)


def encode_title(text: str) -> str:
    return f"base64:{base64.b64encode(text.encode()).decode()}"
