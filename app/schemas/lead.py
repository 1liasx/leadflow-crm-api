from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class LeadStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    WON = "won"
    LOST = "lost"


class LeadBase(BaseModel):
    company_id: int = Field(gt=0)
    contact_id: int | None = Field(default=None, gt=0)
    external_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    title: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: LeadStatus = LeadStatus.NEW
    source: str | None = Field(default=None, max_length=100)

    estimated_value: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    currency: str = Field(
        default="MAD",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    company_id: int | None = Field(default=None, gt=0)
    contact_id: int | None = Field(default=None, gt=0)
    external_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    status: LeadStatus | None = None
    source: str | None = Field(default=None, max_length=100)

    estimated_value: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    )

    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return value.upper()


class LeadRead(LeadBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)