
import uuid
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime, date
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin, utcnow
from .project import Project

class EVirtualAssetType(enum.Enum):
    character = "character"
    prop = "prop"
    scene = "scene"
    camera = "camera"


class VirtualAsset(BaseMixin, AttrMixin, ProjectScopedDataMixin):
    """ """

    __tablename__ = "virtual_asset_t"
    __table_args__ = (
        UniqueConstraint("code", "project_id",
                         name="virtual_asset_code_project_uix"),
    )
    code: str = Field(max_length=32, nullable=False)
    client_name: Optional[str] = Field(max_digits=128)
    
    type_ = Field(Enum(EVirtualAssetType), nullable=False)
    
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Optional[Project] = Relationship(back_populates="virtual_assets")
    revisions: VirtualAssetRevision = Relationship(
        order_by="desc(VirtualAssetRevision.number)",
        back_populates="virtual_asset",
    )

class VirtualAssetRevision(BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin):
    """ """

    OFFICIAL = "official"

    __tablename__ = "virtual_asset_revision_t"
    __table_args__ = (
        UniqueConstraint(
            "virtual_asset_id",
            "number",
            name="virtual_asset_revision_virtual_asset_id_number_uix",
        ),
    )
    number: int = Field(nullable=False, ge=1)
    tags: list[str] = Field(default=[])
    virtual_asset_id: uuid.UUID = Field(foreign_key="virtual_asset_t.id", nullable=False)
    virtual_asset: VirtualAsset = Relationship(
        back_populates="revisions", lazy="joined"
    )
    project_id = Field(ForeignKey("project_t.id"), nullable=False)
    project = Relationship("Project")
    source_mappings = Relationship(
        "Mapping",
        back_populates="source",
        primaryjoin="VirtualAssetRevision.id==Mapping.source_id",
    )
    target_mappings = Relationship(
        "Mapping",
        back_populates="target",
        primaryjoin="VirtualAssetRevision.id==Mapping.target_id",
    )
    resources = Relationship(
        "Resource", secondary="resource_assoc_t", backref="virtual_asset_revisions"
    )
