import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc

if TYPE_CHECKING:
    from .virtual_asset import VirtualAssetRevision


class Mapping(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True):
    """Describes a relationship between a source skeleton and a target
    skeleton, used for retargeting motion. Many-to-Many
    """

    __tablename__ = "mapping_t"
    __table_args__ = (
        UniqueConstraint(
            "name", "source_id", "target_id", name="mapping_name_source_target_uix"
        ),
    )
    name: str = Field(max_length=128)
    fqn: str = Field(max_length=256)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    source_id: uuid.UUID = Field(
        # foreign_key="virtual_asset_revision_t.id",
        nullable=False
    )
    source: "VirtualAssetRevision" = Relationship(
        back_populates="source_mappings",
        # foreign_keys=[source_id],
        # lazy="joined"
    )
    target_id: uuid.UUID = Field(
        # foreign_key="virtual_asset_revision_t.id",
        nullable=False
    )
    target: "VirtualAssetRevision" = Relationship(
        # foreign_keys=[target_id],
        back_populates="target_mappings",
        # lazy="joined"
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="mapping"
    )
