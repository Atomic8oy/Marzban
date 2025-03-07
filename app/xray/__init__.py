from typing import Dict

from app import on_startup
from app.models.host import ProxyHostSecurity
from app.utils.store import DictStorage
from app.xray import operations
from app.xray.config import XRayConfig
from app.xray.core import XRayCore
from app.xray.node import XRayNode
from config import XRAY_JSON


config = XRayConfig(XRAY_JSON)

nodes: Dict[int, XRayNode] = {}


@DictStorage
def hosts(storage: dict):
    from app.db import GetDB, crud

    storage.clear()
    with GetDB() as db:
        db_hosts = crud.get_hosts(db)

        for host in db_hosts:
            if host.is_disabled or (config.get_inbound(host.inbound_tag) is None):
                continue

            storage[host.id] = {
                "remark": host.remark,
                "inbound_tag": host.inbound_tag,
                "address": [i.strip() for i in host.address.split(",")] if host.address else [],
                "port": host.port,
                "path": host.path if host.path else None,
                "sni": [i.strip() for i in host.sni.split(",")] if host.sni else [],
                "host": [i.strip() for i in host.host.split(",")] if host.host else [],
                "alpn": host.alpn.value,
                "fingerprint": host.fingerprint.value,
                # None means the tls is not specified by host itself and
                #  complies with its inbound's settings.
                "tls": None if host.security == ProxyHostSecurity.inbound_default else host.security.value,
                "allowinsecure": host.allowinsecure,
                "fragment_settings": host.fragment_settings,
                "noise_settings": host.noise_settings,
                "random_user_agent": host.random_user_agent,
                "use_sni_as_host": host.use_sni_as_host,
                "http_headers": host.http_headers,
                "mux_settings": host.mux_settings,
                "transport_settings": host.transport_settings,
            }


on_startup(hosts.update)


__all__ = [
    "config",
    "hosts",
    "nodes",
    "operations",
    "XRayConfig",
    "XRayCore",
    "XRayNode",
]
