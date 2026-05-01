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


class CaptureLoad(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):

    LIVE = "live"

    __tablename__ = "capture_load_t"
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    name: str = Field(max_length=128)
    tags: Optional[list[str]] = Feild(default=[])
    volume_id: Optional[uuid.UUID] = Field(foreign_key="volume_t.id")
    volume: Optional["Volume"] = Relationship(back_populates="capture_loads")
    take_id: Optional[uuid.UUID] = Field(foreign_key="take_t.id")
    take: Optional["Take"] = Relationship(back_populates="capture_loads")
    entries: list["CaptureLoadEntry"] = Relationship(
        back_populates="capture_load", order_by="CaptureLoadEntry.index.asc()"
    )


class CaptureLoadEntry(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ """

    __tablename__ = "capture_load_entry_t"
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    capture_load_id: uuid.UUID = Field(
        foreign_key="capture_load_t.id", nullable=False)
    capture_load: CaptureLoad = Relationship(back_populates="entries")
    solver_setup_id: Optional[uuid.UUID] = Field(
        foreign_key="solver_setup_t.id", default=None
    )
    solver_setup: Optional["SolverSetup"] = Relationship()
    mapping_id: Optional[uuid.UUID] = Field(
        foreign_key="mapping_t.id", default=None)
    mapping: Optional["Mapping"] = Relationship()
    index: Optional[int] = Field(nullable=False, ge=1)
    is_enabled: Optional[bool] = Field(default=True)
    has_body: Optional[bool] = Field(default=True)
    has_facial: Optional[bool] = Field(default=False)
    has_fingers: Optional[bool] = Field(default=False)
    versions: Optional[list["CaptureLoadEntryVersion"]] = Relationship(
        back_populates="capture_load_entry",
        order_by="CaptureLoadEntryVersion.name.asc()",
    )


class CaptureLoadEntryVersion(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):
    __tablename__ = "capture_load_entry_version_t"
    __table_args__ = UniqueConstraint(
        "name",
        "capture_load_entry_id",
        "version_id",
        name="capture_load_entry_version_name_capture_load_id_version_id_uix",
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    name: str = Field(max_length=64)
    capture_load_entry_id: uuid.UUID = Field(
        foreign_key="capture_load_entry_t.id", nullable=False
    )
    capture_load_entry: "CaptureLoadEntry" = Relationship(
        back_populates="versions", order_by="CaptureLoadEntryVersion.name.asc()"
    )
    version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    version: "Version" = Relationship()
