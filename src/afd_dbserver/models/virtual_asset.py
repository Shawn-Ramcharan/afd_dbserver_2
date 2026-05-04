
import uuid
import enum
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import Enum as SqlaEnum
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, Column, distinct, select)

from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc
if TYPE_CHECKING:
    from .mapping import Mapping

class EVirtualAssetType(enum.Enum):
    character = "character"
    prop = "prop"
    scene = "scene"
    camera = "camera"


class VirtualAsset(BaseMixin, AttrMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ """

    __tablename__ = "virtual_asset_t"
    __table_args__ = (
        UniqueConstraint("code", "project_id",
        name="virtual_asset_code_project_uix"),
    )
    code: str = Field(max_length=32, nullable=False)
    client_name: Optional[str] = Field(max_digits=128)
    type_: EVirtualAssetType = Field(
        sa_column=Column(SqlaEnum(EVirtualAssetType, name='evirtualassettype'), nullable=False)
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship(back_populates="virtual_assets")
    revisions: list["VirtualAssetRevision"] = Relationship(
        # order_by="desc(VirtualAssetRevision.number)",
        back_populates="virtual_asset",
    )

class VirtualAssetRevision(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """ """

    OFFICIAL: ClassVar = "official"

    __tablename__ = "virtual_asset_revision_t"
    __table_args__ = (
        UniqueConstraint(
            "virtual_asset_id",
            "number",
            name="virtual_asset_revision_virtual_asset_id_number_uix",
        ),
    )
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    number: int = Field(nullable=False, ge=1)
    # tags: Optional[list[str]] = Field(default=None)
    virtual_asset_id: uuid.UUID = Field(foreign_key="virtual_asset_t.id", nullable=False)
    virtual_asset: VirtualAsset = Relationship(
        back_populates="revisions",
        sa_relationship_kwargs=dict(lazy="joined")
    )
    source_mappings: list["Mapping"] = Relationship(
        back_populates="source",
        sa_relationship_kwargs=dict(primaryjoin="VirtualAssetRevision.id==Mapping.source_id")
    )
    target_mappings: list["Mapping"] = Relationship(
        back_populates="target",
        sa_relationship_kwargs=dict(primaryjoin="VirtualAssetRevision.id==Mapping.target_id")
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="virtual_asset_revision"
    )
