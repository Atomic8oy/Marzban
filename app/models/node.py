from cryptography.x509 import load_pem_x509_certificate
import re

from pydantic import ConfigDict, BaseModel, Field, field_validator

from app.db.models import NodeConnectionType, NodeStatus


# Basic PEM format validation
CERT_PATTERN = r"-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----"
KEY_PATTERN = r"-----BEGIN (?:RSA )?PRIVATE KEY-----"


class NodeSettings(BaseModel):
    min_node_version: str = "v1.0.0"
    certificate: str


class Node(BaseModel):
    name: str
    address: str
    port: int = 62050
    usage_coefficient: float = Field(gt=0, default=1.0)
    connection_type: NodeConnectionType
    server_ca: str
    keep_alive: int
    max_logs: int
    core_config_id: int | None = None


class NodeCreate(Node):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "DE node",
                "address": "192.168.1.1",
                "port": 62050,
                "usage_coefficient": 1,
                "server_ca": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                "connection_type": "grpc",
                "keep_alive": 60,
                "max_logs": 1000,
                "core_config_id": 1,
            }
        }
    )

    @field_validator("server_ca")
    @classmethod
    def validate_certificate(cls, v: str | None) -> str | None:
        if v is None:
            return None

        v = v.strip()

        # Check for PEM certificate format
        if not re.search(CERT_PATTERN, v, re.DOTALL):
            raise ValueError("Invalid certificate format - must contain PEM certificate blocks")

        # Check for private key material
        if re.search(KEY_PATTERN, v):
            raise ValueError("Certificate contains private key material")

        if len(v) > 2048:
            raise ValueError("Certificate too large (max 2048 characters)")

        try:
            load_pem_x509_certificate(v.encode("utf-8"))
            pass
        except Exception:
            raise ValueError("Invalid certificate structure")

        return v

    @field_validator("max_logs")
    @classmethod
    def validate_max_logs(cls, v: int | None) -> int | None:
        if v is None:
            return None

        if v < 1:
            raise ValueError("Max logs cant be lower than 1")

        return v


class NodeModify(NodeCreate):
    name: str | None = None
    address: str | None = None
    port: int | None = None
    api_port: int | None = None
    status: NodeStatus | None = None
    usage_coefficient: float | None = None
    server_ca: str | None = None
    connection_type: NodeConnectionType | None = None
    keep_alive: int | None = None
    max_logs: int | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "DE node",
                "address": "192.168.1.1",
                "port": 62050,
                "status": "disabled",
                "usage_coefficient": 1.0,
                "connection_type": "grpc",
                "server_ca": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                "keep_alive": 60,
                "max_logs": 1000,
                "core_config_id": 1,
            }
        }
    )


class NodeResponse(Node):
    id: int
    xray_version: str | None = None
    node_version: str | None = None
    status: NodeStatus
    message: str | None = None
    model_config = ConfigDict(from_attributes=True)
