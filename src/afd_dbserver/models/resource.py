# from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlalchemy import ARRAY, Text, String
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
    from .virtual_asset import VirtualAssetRevision


class ResourceAssoc(IdMixin, SQLModel, table=True):
    __tablename__ = "resource_assoc_t"
    resource_id: uuid.UUID = Field(foreign_key="resource_t.id", unique=True)
    resource: "Resource" = Relationship()
    # =======================
    # NOTE: this is not for saying this resource is
    # project scoped. this is just for associating
    # resource to the project since projects can have
    # resources against it. Treat this attr/relationship
    # like any other attrs in the table like solver_setup_id,
    # mapping_id, etc.
    project_id: Optional[uuid.UUID] = Field(foreign_key="project_t.id", default=None)
    project: "Project" = Relationship()
    # =======================
    solver_setup_id: Optional[uuid.UUID] = Field(foreign_key="solver_setup_t.id", default=None)
    solver_setup: "SolverSetup" = Relationship()
    virtual_asset_revision_id: Optional[uuid.UUID] = Field(
        foreign_key="virtual_asset_revision_t.id",
        default=None
    )
    virtual_asset_revision: "VirtualAssetRevision" = Relationship()
    mapping_id: Optional[uuid.UUID] = Field(foreign_key="mapping_t.id", default=None)
    mapping: "Mapping" = Relationship()
    session_id: Optional[uuid.UUID] = Field(foreign_key="session_t.id", default=None)
    session: "Session" = Relationship()
    volume_id: Optional[uuid.UUID] = Field(foreign_key="volume_t.id", default=None)
    volume: "Volume" = Relationship()
    device_id: Optional[uuid.UUID] = Field(foreign_key="device_t.id", default=None)
    device: "Device" = Relationship()
    take_id: Optional[uuid.UUID] = Field(foreign_key="take_t.id", default=None)
    take: "Take" = Relationship()
    take_select_id: Optional[uuid.UUID] = Field(foreign_key="take_select_t.id", default=None)
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
    name: str = Field(max_length=64, nullable=False)
    group: str = Field(max_length=64, nullable=False)
    uri: Optional[str] = Field(max_length=256)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: "Project" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    versions: list["Version"] = Relationship(
        back_populates="resource"
    )
    virtual_asset_revision: "VirtualAssetRevision" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    mapping: "Mapping" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    session: "Session" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    solver_setup: "SolverSetup" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    device: "Device" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    take: "Take" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    take_select: "TakeSelect" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )
    volume: "Volume" = Relationship(
        back_populates="resources",
        link_model=ResourceAssoc
    )

    PROJECT_ASSOC_CLS: ClassVar = ResourceAssoc


class Version(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):

    LATEST: ClassVar = "latest"
    OFFICIAL: ClassVar = "official"

    __tablename__ = "version_t"
    number: Optional[int] = Field(ge=1)
    tags: Optional[list[str]] = Field(default=None, sa_column=Column('tags', ARRAY(Text())))
    description: Optional[str] = Field(max_length=1024, default=None)
    is_committed: Optional[bool] = Field(default=False)
    uri: Optional[str] = Field(max_length=256)
    resource_id: uuid.UUID = Field(foreign_key="resource_t.id", nullable=False)
    resource: Resource = Relationship(back_populates="versions")
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: "Project" = Relationship()
    # outgoing_links: list["VersionLink"] = Relationship(
    #     back_populates="from_version",
    #     # foreign_key="from_version_id"
    #     # link_model=VersionLink,
    #     sa_relationship_kwargs={
    #         "foreign_keys": ["from_version_id"],
    #     }
    # )
    # incoming_links: list["VersionLink"] = Relationship(
    #     back_populates="to_version",
    #     # foreign_keys=["to_version_id"]
    #     # link_model=VersionLink,
    #     sa_relationship_kwargs={
    #         # "foreign_keys": ["to_version_id"],
    #     }
    # )


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
    # from_version: Version = Relationship(
    #     back_populates="outgoing_links",
    #     link_model=Version,
    #     sa_relationship_kwargs={
    #         # "foreign_keys": ["from_version_id"]
    #     }
    # )
    to_version_id: uuid.UUID = Field(foreign_key="version_t.id", nullable=False)
    # to_version: Version = Relationship(
    #     back_populates="incoming_links",
    #     link_model=Version,
    #     sa_relationship_kwargs={
    #         # "foreign_keys": ["to_version_id"]
    #     }
    # )
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
    item: "Item" = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined"
        }
    )
    PROJECT_PARENT_CLS: ClassVar = Version
    PROJECT_CLS_ATTR: ClassVar = "version_id"


class Item(BaseMixin, AttrMixin, SQLModel, table=True):
    __tablename__ = "item_t"
    location_hash: Optional[bytes] = Field(
        default=None, unique=True, index=True, nullable=False
    )
    location: Optional[str] = Field(
        max_length=512,
        default=None,
        sa_column=Column('_location', String(512))
    )
    # versions: list[Version] = Relationship(
    #     link_model=ResourceAssoc,
    #     back_populates="item",
    #     sa_relationship_kwargs={
    #         "viewonly": True
    #     }
    # )
