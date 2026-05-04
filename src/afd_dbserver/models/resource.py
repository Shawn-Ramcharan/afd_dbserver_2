from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint, PrimaryKeyConstraint
from datetime import datetime, date
from sqlmodel import Column, Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import (
    IdMixin,
    BaseMixin,
    AttrMixin,
    ProjectScopedDataMixin,
    ProjectScopedAssocMixin,
    ProjectScopedParentMixin,
    utcnow,
)

if TYPE_CHECKING:
    from .project import Project
    from .volume import Volume
    from .session import Session
    from .take import Take
    from .mapping import Mapping
    from .solver_setup import SolverSetup
    from .take_select import TakeSelect
    from .device import Device


class ResourceAssoc(IdMixin, SQLModel, table=True):
    __tablename__ = "resource_assoc_t"


    # __table_args__ = (
        # ForeignKeyConstraint(['device_id'], ['device_t.id'], name='fk_resource_assoc_t_device_id_device_t'),
        # ForeignKeyConstraint(['mapping_id'], ['mapping_t.id'], name='fk_resource_assoc_t_mapping_id_mapping_t'),
        # ForeignKeyConstraint(['project_id'], ['project_t.id'], name='fk_resource_assoc_t_project_id_project_t'),
        # ForeignKeyConstraint(['resource_id'], ['resource_t.id'], name='fk_resource_assoc_t_resource_id_resource_t'),
        # ForeignKeyConstraint(['session_id'], ['session_t.id'], name='fk_resource_assoc_t_session_id_session_t'),
        # ForeignKeyConstraint(['solver_setup_id'], ['solver_setup_t.id'], name='fk_resource_assoc_t_solver_setup_id_solver_setup_t'),
        # ForeignKeyConstraint(['take_id'], ['take_t.id'], name='fk_resource_assoc_t_take_id_take_t'),
        # ForeignKeyConstraint(['take_select_id'], ['take_select_t.id'], name='fk_resource_assoc_t_take_select_id_take_select_t'),
        # ForeignKeyConstraint(['virtual_asset_revision_id'], ['virtual_asset_revision_t.id'], name='fk_resource_assoc_t_virtual_asset_revision_id_virtual_a_e661'),
        # ForeignKeyConstraint(['volume_id'], ['volume_t.id'], name='fk_resource_assoc_t_volume_id_volume_t'),
        # PrimaryKeyConstraint('id', name='pk_resource_assoc_t'),
        # UniqueConstraint('resource_id', name='uq_resource_assoc_t_resource_id')
    # )


    resource_id: uuid.UUID = Field(foreign_key="resource_t.id", unique=True)
    resource: "Resource" = Relationship()
    project_id: Optional[uuid.UUID] = Field(foreign_key="project_t.id")
    project: Project = Relationship()
    solver_setup_id: Optional[uuid.UUID] = Field(foreign_key="solver_setup_t.id")
    solver_setup: "SolverSetup" = Relationship()
    virtual_asset_revision_id: Optional[uuid.UUID] = Field(
        foreign_key="virtual_asset_revision_t.id"
    )
    virtual_asset_revision: "VirtualAssetRevision" = Relationship()
    mapping_id: Optional[uuid.UUID] = Field(foreign_key="mapping_t.id")
    mapping: "Mapping" = Relationship()
    session_id: Optional[uuid.UUID] = Field(foreign_key="session_t.id")
    session: "Session" = Relationship()
    volume_id: Optional[uuid.UUID] = Field(foreign_key="volume_t.id")
    volume: "Volume" = Relationship()
    device_id: Optional[uuid.UUID] = Field(foreign_key="device_t.id")
    device: "Device" = Relationship()
    take_id: Optional[uuid.UUID] = Field(foreign_key="take_t.id")
    take: "Take" = Relationship()
    take_select_id: Optional[uuid.UUID] = Field(foreign_key="take_select_t.id")
    take_select: "TakeSelect" = Relationship()


class Resource(
    BaseMixin,
    AttrMixin,
    ProjectScopedDataMixin,
    ProjectScopedAssocMixin,
    SQLModel,
    table=True,
):
    __tablename__ = "resource_t"
    name: str = Field(max_length=64)
    group: str = Field(max_length=64)
    uri: Optional[str] = Field(max_length=256)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    PROJECT_ASSOC_CLS: ClassVar = ResourceAssoc


class Version(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):

    LATEST: ClassVar = "latest"
    OFFICIAL: ClassVar = "official"

    __tablename__ = "version_t"
    number: Optional[int] = Field(ge=1)
    # FIXME: find out why optional list of dreing dont work
    # tags: Optional[list[str]] = Field(default=None)
    description: Optional[str] = Field(max_length=1024)
    is_committed: Optional[bool] = Field(default=False)
    uri: Optional[str] = Field(max_length=256)
    resource_id: uuid.UUID = Field(foreign_key="resource_t.id", nullable=False)
    resource: "Resource" = Relationship(back_populates="versions")
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    outgoing_links: list[VersionLink] = Relationship(
        back_populates="from_version",
        # link_model=VersionLink,
        # foreign_keys=["from_version_id"],
    )
    incoming_links: list[VersionLink] = Relationship(
        back_populates="to_version",
        # link_model=VersionLink,
        # foreign_keys=["to_version_id"],
    )


class VersionLink(BaseMixin, AttrMixin, ProjectScopedParentMixin, SQLModel, table=True):
    __tablename__ = "version_link_t"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "from_version_id",
            "to_version_id",
            name="version_link_name_from_to_uix",
        ),
    )
    name: str = Field(max_length=1024)
    from_version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    from_version: Version = Relationship(
        back_populates="outgoing_links",
        link_model=Version,
        # foreign_keys=from_version_id
    )
    to_version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    to_version: Version = Relationship(
        back_populates="incoming_links",
        link_model=Version,
        # foreign_keys=[to_version_id]
    )
    PROJECT_PARENT_CLS: ClassVar = Version
    PROJECT_CLS_ATTR: ClassVar = "to_version_id"


class ItemAssoc(IdMixin, ProjectScopedParentMixin, SQLModel, table=True):
    __tablename__ = "item_assoc_t"
    __table_args__ = (
        UniqueConstraint("version_id", "name", name="version_name_item_uix"),
    )
    version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    item_id: uuid.UUID = Field(foreign_key="item_t.id", nullable=False)
    name: Optional[str] = Field(max_length=64)
    uri: Optional[str] = Field(max_length=256)
    version: Version = Relationship()
    item: Item = Relationship()#lazy="joined")
    PROJECT_PARENT_CLS: ClassVar = Version
    PROJECT_CLS_ATTR: ClassVar = "version_id"


class Item(BaseMixin, AttrMixin, SQLModel, table=True):
    __tablename__ = "item_t"
    location_hash: Optional[bytes] = Field(
        default=None, unique=True, index=True, nullable=False
    )
    # location_: Optional[str] = Field(max_length=512, sa_column=Column("_location"), default=None)
