from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, field_validator

from .validators import NumericValidatorMixin, PasswordValidator


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminBaseInfo(BaseModel):
    """Base model containing the core admin identification fields."""

    username: str
    telegram_id: int | None = None
    discord_webhook: str | None = None
    sub_domain: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminDetails(AdminBaseInfo):
    """Complete admin model with all fields for database representation and API responses."""

    is_sudo: bool
    users_usage: int = 0
    is_disabled: bool = False
    sub_template: str | None = None
    profile_title: str | None = None
    support_url: str | None = None
    lifetime_used_traffic: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("users_usage", mode="before")
    def cast_to_int(cls, v):
        return NumericValidatorMixin.cast_to_int(v)


class AdminModify(BaseModel):
    password: str | None = None
    is_sudo: bool
    telegram_id: int | None = None
    discord_webhook: str | None = None
    is_disabled: bool | None = None
    sub_template: str | None = None
    sub_domain: str | None = None
    profile_title: str | None = None
    support_url: str | None = None

    @property
    def hashed_password(self):
        if self.password:
            return pwd_context.hash(self.password)

    @field_validator("discord_webhook")
    @classmethod
    def validate_discord_webhook(cls, value):
        if value and not value.startswith("https://discord.com"):
            raise ValueError("Discord webhook must start with 'https://discord.com'")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None):
        return PasswordValidator.validate_password(value)


class AdminCreate(AdminModify):
    """Model for creating new admin accounts requiring username and password."""

    username: str
    password: str


class AdminInDB(AdminDetails):
    hashed_password: str

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.hashed_password)


class AdminValidationResult(BaseModel):
    username: str
    is_sudo: bool
    is_disabled: bool
