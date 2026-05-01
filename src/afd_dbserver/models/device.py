import uuid
from typing import Optional
from sqlalchemy.schema import UniqueConstraint
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .project import Project
from .appliance import Appliance


class Device(BaseMixin, AttrMixin, ProjectScopedDataMixin, ResourceMixin, SQLModel, table=True):
    """An instance of a recording device. Unique to a Session."""

    __tablename__ = "device_t"
    __table_args__ = (
        UniqueConstraint("code", "volume_id", name="device_code_volume_uix"),
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    name: str = Field(max_length=32, nullable=False)
    sample_rate: Optional[float] = Field(default=30.0)
    appliance_id: uuid.UUID = Field(foreign_key="appliance_t.id")
    appliance: Appliance = Relationship()
    volume_id: uuid.UUID = Field(foreign_key="volume_t.id", nullable=False)
    volume: "Volume" = Relationship(back_populates="devices")
    resources: list["Resource"] = Relationship(
        link_model="resource_assoc_t", back_populates="device"
    )
