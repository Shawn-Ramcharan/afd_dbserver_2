import uuid
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .project import Project


class Volume(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin):
    """ """

    __tablename__ = "volume_t"
    __table_args__ = (
        UniqueConstraint("code", "session_id", name="volume_code_session_uix"),
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Optional[Project] = Relationship()
    code: uuid.UUID = Field(max_length=32, nullable=False)
    session_id: uuid.UUID = Field(foreign_key="session_t.id", nullable=False)
    session: Optional[Session] = Relationship(back_populates="volumes")
    devices: list[Device] = Relationship(
        back_populates="volume", order_by="Device.code.asc()"
    )
    capture_loads: list[CaptureLoad] = Relationship(
        back_populates="volume",
        order_by=desc(text("capture_load_t.creation_date")),
    )
    resources: list[Resource] = Relationship(
        link_model="resource_assoc_t", back_populates="volume"
    )
