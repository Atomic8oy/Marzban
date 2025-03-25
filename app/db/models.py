import os
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
    func,
    event,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import select, text
from sqlalchemy.ext.compiler import compiles
from app.db.base import Base


class CaseSensitiveString(String):
    def __init__(self, length=None):
        super(CaseSensitiveString, self).__init__(length)


# Modify how this type is handled for each dialect
@compiles(CaseSensitiveString, "sqlite")
def compile_cs_sqlite(element, compiler, **kw):
    return f"VARCHAR({element.length}) COLLATE BINARY"  # BINARY is case-sensitive in SQLite


@compiles(CaseSensitiveString, "postgresql")
def compile_cs_postgresql(element, compiler, **kw):
    return f'VARCHAR({element.length}) COLLATE "C"'  # "C" collation is case-sensitive


@compiles(CaseSensitiveString, "mysql")
def compile_cs_mysql(element, compiler, **kw):
    return f"VARCHAR({element.length}) COLLATE utf8mb4_bin"  # utf8mb4_bin is case-sensitive


inbounds_groups_association = Table(
    "inbounds_groups_association",
    Base.metadata,
    Column("inbound_id", ForeignKey("inbounds.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
)

users_groups_association = Table(
    "users_groups_association",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("groups_id", ForeignKey("groups.id"), primary_key=True),
)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(34), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    users: Mapped[List["User"]] = relationship(back_populates="admin")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_sudo: Mapped[bool] = mapped_column(default=False)
    password_reset_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, default=None)
    discord_webhook: Mapped[Optional[str]] = mapped_column(String(1024), default=None)
    users_usage: Mapped[int] = mapped_column(BigInteger, default=0)
    is_disabled: Mapped[bool] = mapped_column(server_default="0", default=False)
    usage_logs: Mapped[List["AdminUsageLogs"]] = relationship(back_populates="admin", lazy="selectin")
    sub_template: Mapped[Optional[str]] = mapped_column(String(1024), default=None)
    sub_domain: Mapped[Optional[str]] = mapped_column(String(256), default=None)
    profile_title: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    support_url: Mapped[Optional[str]] = mapped_column(String(1024), default=None)

    @hybrid_property
    def reseted_usage(self) -> int:
        return int(sum([log.used_traffic_at_reset for log in self.usage_logs]))

    @reseted_usage.expression
    def reseted_usage(cls):
        return (
            select(func.sum(AdminUsageLogs.used_traffic_at_reset))
            .where(AdminUsageLogs.admin_id == cls.id)
            .label("reseted_usage")
        )

    @property
    def lifetime_used_traffic(self) -> int:
        return self.reseted_usage + self.users_usage


class AdminUsageLogs(Base):
    __tablename__ = "admin_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"))
    admin: Mapped["Admin"] = relationship(back_populates="usage_logs")
    used_traffic_at_reset: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reset_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ReminderType(str, Enum):
    expiration_date = "expiration_date"
    data_usage = "data_usage"


class UserStatus(str, Enum):
    active = "active"
    disabled = "disabled"
    limited = "limited"
    expired = "expired"
    on_hold = "on_hold"


class UserDataLimitResetStrategy(str, Enum):
    no_reset = "no_reset"
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(CaseSensitiveString(34), unique=True, index=True)
    proxy_settings: Mapped[Dict[str, Any]] = mapped_column(JSON(True), server_default=text("'{}'"), default=lambda: {})
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus), default=UserStatus.active)
    used_traffic: Mapped[int] = mapped_column(BigInteger, default=0)
    node_usages: Mapped[List["NodeUserUsage"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="joined"
    )
    notification_reminders: Mapped[List["NotificationReminder"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="joined"
    )
    data_limit: Mapped[Optional[int]] = mapped_column(BigInteger, default=None)
    data_limit_reset_strategy: Mapped[UserDataLimitResetStrategy] = mapped_column(
        SQLEnum(UserDataLimitResetStrategy),
        default=UserDataLimitResetStrategy.no_reset,
    )
    usage_logs: Mapped[List["UserUsageResetLogs"]] = relationship(back_populates="user", lazy="selectin")
    expire: Mapped[Optional[datetime]] = mapped_column(default=None)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id"), default=None)
    admin: Mapped["Admin"] = relationship(back_populates="users", lazy="selectin")
    sub_revoked_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    sub_updated_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    sub_last_user_agent: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    note: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    online_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    on_hold_expire_duration: Mapped[Optional[int]] = mapped_column(BigInteger, default=None)
    on_hold_timeout: Mapped[Optional[datetime]] = mapped_column(default=None)
    auto_delete_in_days: Mapped[Optional[int]] = mapped_column(default=None)
    edit_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    last_status_change: Mapped[Optional[datetime]] = mapped_column(default=datetime.utcnow)

    next_plan: Mapped[Optional["NextPlan"]] = relationship(
        uselist=False, back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    groups: Mapped[List["Group"]] = relationship(
        secondary=users_groups_association, back_populates="users", lazy="selectin"
    )

    @hybrid_property
    def reseted_usage(self) -> int:
        return int(sum([log.used_traffic_at_reset for log in self.usage_logs]))

    @reseted_usage.expression
    def reseted_usage(cls):
        return (
            select(func.sum(UserUsageResetLogs.used_traffic_at_reset))
            .where(UserUsageResetLogs.user_id == cls.id)
            .label("reseted_usage")
        )

    @property
    def lifetime_used_traffic(self) -> int:
        return int(sum([log.used_traffic_at_reset for log in self.usage_logs]) + self.used_traffic)

    @property
    def last_traffic_reset_time(self):
        return self.usage_logs[-1].reset_at if self.usage_logs else self.created_at

    def inbounds(self, active_inbounds: list[str]) -> list[str]:
        """Returns a flat list of all included inbound tags across all proxies"""
        included_tags = []
        for group in self.groups:
            if group.is_disabled:
                continue
            tags = group.inbound_tags
            for inbound in active_inbounds:
                if inbound in tags:
                    included_tags.append(inbound)
        return included_tags

    @property
    def group_ids(self):
        return [group.id for group in self.groups]

    @property
    def group_names(self):
        return [group.name for group in self.groups]


template_group_association = Table(
    "template_group_association",
    Base.metadata,
    Column("user_template_id", ForeignKey("user_templates.id")),
    Column("group_id", ForeignKey("groups.id")),
)


class NextPlan(Base):
    __tablename__ = "next_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_templates.id"))
    data_limit: Mapped[int] = mapped_column(BigInteger, default=0)
    expire: Mapped[Optional[int]] = mapped_column(default=None)
    add_remaining_traffic: Mapped[bool] = mapped_column(default=False, server_default="0")
    fire_on_either: Mapped[bool] = mapped_column(default=True, server_default="0")

    user: Mapped["User"] = relationship(back_populates="next_plan")
    user_template: Mapped[Optional["UserTemplate"]] = relationship(back_populates="next_plans")


class UserTemplate(Base):
    __tablename__ = "user_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    data_limit: Mapped[int] = mapped_column(BigInteger, default=0)
    expire_duration: Mapped[int] = mapped_column(BigInteger, default=0)  # in seconds
    username_prefix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    username_suffix: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    next_plans: Mapped[List["NextPlan"]] = relationship(back_populates="user_template", cascade="all, delete-orphan")
    groups: Mapped[List["Group"]] = relationship(
        secondary=template_group_association, back_populates="templates", lazy="selectin"
    )

    @property
    def group_ids(self):
        return [group.id for group in self.groups]


class UserUsageResetLogs(Base):
    __tablename__ = "user_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship(back_populates="usage_logs")
    used_traffic_at_reset: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reset_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ProxyInbound(Base):
    __tablename__ = "inbounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    hosts: Mapped[List["ProxyHost"]] = relationship(back_populates="inbound", cascade="all, delete-orphan")
    groups: Mapped[List["Group"]] = relationship(secondary=inbounds_groups_association, back_populates="inbounds")


@event.listens_for(ProxyInbound, "after_delete")
def delete_association_rows(mapper, connection, target):
    connection.execute(
        inbounds_groups_association.delete().where(inbounds_groups_association.c.inbound_id == target.id)
    )


class ProxyHostSecurity(str, Enum):
    inbound_default = "inbound_default"
    none = "none"
    tls = "tls"


ProxyHostALPN = Enum(
    "ProxyHostALPN",
    {
        "none": "",
        "h3": "h3",
        "h2": "h2",
        "http/1.1": "http/1.1",
        "h3,h2,http/1.1": "h3,h2,http/1.1",
        "h3,h2": "h3,h2",
        "h2,http/1.1": "h2,http/1.1",
    },
)
ProxyHostFingerprint = Enum(
    "ProxyHostFingerprint",
    {
        "none": "",
        "chrome": "chrome",
        "firefox": "firefox",
        "safari": "safari",
        "ios": "ios",
        "android": "android",
        "edge": "edge",
        "360": "360",
        "qq": "qq",
        "random": "random",
        "randomized": "randomized",
    },
)


class ProxyHost(Base):
    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True)
    remark: Mapped[str] = mapped_column(String(256), unique=False, nullable=False)
    address: Mapped[str] = mapped_column(String(256), unique=False, nullable=False)
    port: Mapped[Optional[int]] = mapped_column(nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(256), unique=False, nullable=True)
    sni: Mapped[Optional[str]] = mapped_column(String(1000), unique=False, nullable=True)
    host: Mapped[Optional[str]] = mapped_column(String(1000), unique=False, nullable=True)
    security: Mapped[ProxyHostSecurity] = mapped_column(
        SQLEnum(ProxyHostSecurity),
        unique=False,
        default=ProxyHostSecurity.inbound_default,
    )
    alpn: Mapped[ProxyHostALPN] = mapped_column(
        SQLEnum(ProxyHostALPN),
        unique=False,
        default=ProxyHostSecurity.none,
        server_default=ProxyHostSecurity.none.name,
    )
    fingerprint: Mapped[ProxyHostFingerprint] = mapped_column(
        SQLEnum(ProxyHostFingerprint),
        unique=False,
        default=ProxyHostSecurity.none,
        server_default=ProxyHostSecurity.none.name,
    )

    inbound_tag: Mapped[Optional[str]] = mapped_column(
        String(256), ForeignKey("inbounds.tag", ondelete="SET NULL", onupdate="CASCADE"), nullable=True
    )
    inbound: Mapped[Optional["ProxyInbound"]] = relationship(back_populates="hosts")
    allowinsecure: Mapped[Optional[bool]] = mapped_column(nullable=True)
    is_disabled: Mapped[Optional[bool]] = mapped_column(default=False)
    fragment_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON(none_as_null=True), default=None)
    noise_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON(none_as_null=True), default=None)
    random_user_agent: Mapped[bool] = mapped_column(default=False, server_default="0")
    use_sni_as_host: Mapped[bool] = mapped_column(default=False, server_default="0")
    priority: Mapped[int] = mapped_column(nullable=False)
    http_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON(none_as_null=True), default=None)
    transport_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON(none_as_null=True), default=None)
    mux_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON(none_as_null=True), default=None)


class System(Base):
    __tablename__ = "system"

    id: Mapped[int] = mapped_column(primary_key=True)
    uplink: Mapped[int] = mapped_column(BigInteger, default=0)
    downlink: Mapped[int] = mapped_column(BigInteger, default=0)


class JWT(Base):
    __tablename__ = "jwt"

    id: Mapped[int] = mapped_column(primary_key=True)
    secret_key: Mapped[str] = mapped_column(String(64), default=lambda: os.urandom(32).hex())


class TLS(Base):
    __tablename__ = "tls"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(4096), nullable=False)
    certificate: Mapped[str] = mapped_column(String(2048), nullable=False)


class NodeConnectionType(str, Enum):
    grpc = "grpc"
    rest = "rest"


class NodeStatus(str, Enum):
    connected = "connected"
    connecting = "connecting"
    error = "error"
    disabled = "disabled"


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(CaseSensitiveString(256), unique=True)
    address: Mapped[str] = mapped_column(String(256), unique=False, nullable=False)
    port: Mapped[int] = mapped_column(unique=False, nullable=False)
    xray_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[NodeStatus] = mapped_column(SQLEnum(NodeStatus), default=NodeStatus.connecting)
    last_status_change: Mapped[Optional[datetime]] = mapped_column(default=datetime.utcnow)
    message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    uplink: Mapped[int] = mapped_column(BigInteger, default=0)
    downlink: Mapped[int] = mapped_column(BigInteger, default=0)
    user_usages: Mapped[List["NodeUserUsage"]] = relationship(
        back_populates="node", cascade="all, delete-orphan", lazy="selectin"
    )
    usages: Mapped[List["NodeUsage"]] = relationship(back_populates="node", cascade="all, delete-orphan")
    usage_coefficient: Mapped[float] = mapped_column(Float, server_default=text("1.0"), default=1)
    node_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    connection_type: Mapped[NodeConnectionType] = mapped_column(
        SQLEnum(NodeConnectionType),
        unique=False,
        default=NodeConnectionType.grpc,
        server_default=NodeConnectionType.grpc.name,
    )
    server_ca: Mapped[str] = mapped_column(String(2048), nullable=False)
    keep_alive: Mapped[int] = mapped_column(unique=False, default=0)
    max_logs: Mapped[int] = mapped_column(BigInteger, unique=False, default=1000, server_default=text("1000"))


class NodeUserUsage(Base):
    __tablename__ = "node_user_usages"
    __table_args__ = (UniqueConstraint("created_at", "user_id", "node_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(unique=False)  # one hour per record
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="node_usages")
    node_id: Mapped[Optional[int]] = mapped_column(ForeignKey("nodes.id"))
    node: Mapped["Node"] = relationship(back_populates="user_usages")
    used_traffic: Mapped[int] = mapped_column(BigInteger, default=0)


class NodeUsage(Base):
    __tablename__ = "node_usages"
    __table_args__ = (UniqueConstraint("created_at", "node_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(unique=False)  # one hour per record
    node_id: Mapped[Optional[int]] = mapped_column(ForeignKey("nodes.id"))
    node: Mapped["Node"] = relationship(back_populates="usages")
    uplink: Mapped[int] = mapped_column(BigInteger, default=0)
    downlink: Mapped[int] = mapped_column(BigInteger, default=0)


class NotificationReminder(Base):
    __tablename__ = "notification_reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="notification_reminders")
    type: Mapped[ReminderType] = mapped_column(SQLEnum(ReminderType))
    threshold: Mapped[Optional[int]] = mapped_column(default=None)
    expires_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    is_disabled: Mapped[bool] = mapped_column(server_default="0", default=False)

    users: Mapped[List["User"]] = relationship(secondary=users_groups_association, back_populates="groups")
    inbounds: Mapped[List["ProxyInbound"]] = relationship(
        secondary=inbounds_groups_association, back_populates="groups", lazy="selectin"
    )
    templates: Mapped[List["UserTemplate"]] = relationship(
        secondary=template_group_association, back_populates="groups", lazy="selectin"
    )

    @property
    def inbound_ids(self):
        return [inbound.id for inbound in self.inbounds]

    @property
    def inbound_tags(self):
        return [inbound.tag for inbound in self.inbounds]

    @property
    def total_users(self):
        return len(self.users)
