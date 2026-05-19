import uuid
from typing import TYPE_CHECKING, Optional, Self
from sqlalchemy.schema import UniqueConstraint
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .resource import Resource, ResourceAssoc
if TYPE_CHECKING:
    from .project import Project
    from .session import Session
    from .capture_load import CaptureLoad
    from .device import Device

class Volume(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ """

    __tablename__ = "volume_t"
    __table_args__ = (
        UniqueConstraint("code", "session_id", name="volume_code_session_uix"),
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: "Project" = Relationship()
    code: str = Field(max_length=32, nullable=False)
    session_id: uuid.UUID = Field(foreign_key="session_t.id", nullable=False)
    session: Optional["Session"] = Relationship(back_populates="volumes")
    devices: list["Device"] = Relationship(
        back_populates="volume",
        sa_relationship_kwargs={
            "order_by": "Device.code.asc()"
        }
    )
    capture_loads: list["CaptureLoad"] = Relationship(
        back_populates="volume",
        sa_relationship_kwargs={
            "order_by": "CaptureLoad.creation_date.desc()"
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="volume"
    )

    @classmethod
    def create(cls, user_id: str, payload: Self, dbsession: DBSession):
        from .capture_load import CaptureLoad
        vol_model = super(Volume, cls).create(user_id, payload, dbsession)
        cpl_payload = CaptureLoad(
            project_id=payload.project_id,
            name="default",
            tags=["live"],
            volume_id=vol_model.id,
            created_by=user_id,
            modified_by=user_id,
            attrs={}
        )
        CaptureLoad.create(user_id, cpl_payload, dbsession)
        return vol_model

    def delete(self, dbsession: DBSession):
        for device in self.devices:
            device.delete(dbsession)
        self.delete_resources(dbsession)
        dbsession.delete(self)
