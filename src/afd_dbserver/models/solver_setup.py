import uuid
from typing import Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from sqlmodel import Session as DbSession
from sqlmodel import (SQLModel, Field, Relationship, distinct, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .project import Project
from .physical_asset import PhysicalAsset

class SolverSetup(
    BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True
):
    """Describes a relationship between a physical performer or prop and the
    source virtual asset that they are solved onto using motion capture.
    """

    __tablename__ = "solver_setup_t"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "physical_asset_id",
            "virtual_asset_revision_id",
            name="solver_setup_name_physical_virtual_uix",
        ),
    )
    name: str = Field(max_length=128)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    physical_asset_id: uuid.UUID = Field(
        foreign_key="physical_asset_t.id", nullable=False
    )
    physical_asset: PhysicalAsset = Relationship(
        back_populates="solver_setups", lazy="joined"
    )
    virtual_asset_revision_id = Field(
        foreign_key="virtual_asset_revision_t.id", nullable=False
    )
    virtual_asset_revision: "VirtualAssetRevision" = Relationship(lazy="joined")
    resources: "Resource" = Relationship(
        link_model="resource_assoc_t", back_populates="solver_setup"
    )
