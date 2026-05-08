import uuid
from typing import TYPE_CHECKING, ClassVar, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .physical_asset import PhysicalAsset
from .resource import Resource, ResourceAssoc
from ..exc import NotFoundError

if TYPE_CHECKING:
    from .virtual_asset import VirtualAssetRevision

class SolverSetup(
    BaseMixin, AttrMixin, ResourceMixin, ProjectScopedDataMixin, SQLModel, table=True
):
    """Describes a relationship between a physical performer or prop and the
    source virtual asset that they are solved onto using motion capture.
    """

    CLS_ID_ATTR: ClassVar = "solver_setup_id"
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
        back_populates="solver_setups",
        #lazy="joined"
    )
    virtual_asset_revision_id: uuid.UUID = Field(
        foreign_key="virtual_asset_revision_t.id", nullable=False
    )
    virtual_asset_revision: "VirtualAssetRevision" = Relationship()#lazy="joined")
    resources: Resource = Relationship(
        link_model=ResourceAssoc,
        back_populates="solver_setup"
    )

    @classmethod
    def get_all(
        cls,
        dbsession: DBSession,
        project_id: uuid.UUID,
        physical_asset_id: uuid.UUID
    ):
        stmt = select(cls).where(
            cls.project_id == project_id,
            cls.physical_asset_id == physical_asset_id
        ).order_by(cls.name.desc())
        return dbsession.exec(stmt).all()

    @classmethod
    def get(
        cls, dbsession: DBSession,
        physical_asset_id: uuid.UUID,
        virtual_asset_revision_id: uuid.UUID,
        name: str
    ):

        stmt = select(cls).where(
            cls.virtual_asset_revision_id == virtual_asset_revision_id,
            cls.physical_asset_id == physical_asset_id,
            cls.name == name
        )
        try:
            return dbsession.exec(stmt).one()
        except NoResultFound:
            raise NotFoundError(
                f"No {cls.__name__} found with {physical_asset_id=}, {virtual_asset_revision_id=}, {name=}"
            )
