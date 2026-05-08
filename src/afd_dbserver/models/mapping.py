import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from sqlmodel import Session as DBSession
from sqlmodel import (SQLModel, Field, Relationship, select)
from .mixin import BaseMixin, AttrMixin, ProjectScopedDataMixin
from .resource_mixin import ResourceMixin
from .project import Project
from .resource import Resource, ResourceAssoc
from ..exc import NotFoundError

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
    name: Optional[str] = Field(default="default", max_length=128)
    fqn: Optional[str] = Field(max_length=256)
    project_id: uuid.UUID = Field(foreign_key="project_t.id", nullable=False)
    project: Project = Relationship()
    source_id: uuid.UUID = Field(
        foreign_key="virtual_asset_revision_t.id",
        nullable=False,
    )
    source: "VirtualAssetRevision" = Relationship(
        back_populates="source_mappings",
        sa_relationship_kwargs={
            "foreign_keys": "Mapping.source_id",
            "lazy": "joined"
        }
    )
    target_id: uuid.UUID = Field(
        foreign_key="virtual_asset_revision_t.id",
        nullable=False
    )
    target: "VirtualAssetRevision" = Relationship(
        back_populates="target_mappings",
        sa_relationship_kwargs={
            "foreign_keys": "Mapping.target_id",
            "lazy": "joined"
        }
    )
    resources: list["Resource"] = Relationship(
        link_model=ResourceAssoc,
        back_populates="mapping"
    )
    
    @staticmethod
    def get_fqn_string(source_: VirtualAssetRevision, target_: VirtualAssetRevision):
        return f"{source_.virtual_asset.code}_r{source_.number}_to_{target_.virtual_asset.code}_r{target_.number}"

    @classmethod
    def create(cls, payload: SQLModel, dbsession: DBSession):
        # determine the fully-qualified-name (fqn)
        try:
            source_ = VirtualAssetRevision.get_by_id(payload.source_id, dbsession)
            target_ = VirtualAssetRevision.get_by_id(payload.target_id, dbsession)
        except NoResultFound as err:
            raise NotFoundError(err)
        payload.fqn = cls.get_fqn_string(source_, target_)
        model = super(Mapping, cls).create(payload, dbsession)
        return model

    @classmethod
    def get_all(cls, dbsession: DbSession, project_id: uuid.UUID):
        return cls.get_all_by_project(dbsession, project_id)
        # return request.dbsession.query(cls).join(Project).filter(Project.id==project_id).order_by(desc(cls.creation_date)).all()

    @classmethod
    def get(
        cls,
        dbsession: DBSession,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        name: str
    ):
        stmt = select(Mapping).where(
            Mapping.source_id == source_id,
            Mapping.target_id == target_id,
            Mapping.name == name
        )
        try:
            return dbsession.exec(stmt).one()
        except NoResultFound:
            raise NotFoundError(f"No Mapping matching parameters "
                f"source_id={source_id}, "
                f"target_id={target_id}, "
                f"name={name} found.")

    def update(cls, id_: uuid.UUID, payload: SQLModel, dbsession: DBSession):
        source_id = getattr(payload, "source_id", None)
        target_id = getattr(payload, "target_id", None)
        cur_mapping = cls.get_by_id(id_, dbsession)
        if source_id or target_id:
            if source_id:
                source_ = VirtualAssetRevision.get_by_id(source_id, dbsession)
            else:
                source_ = cur_mapping.source
            if target_id:
                target_ = VirtualAssetRevision.get_by_id(target_id, dbsession)
            else:
                target_ = cur_mapping.target
            fqn_ = cls.get_fqn_string(source_, target_)
            setattr(payload, "fqn", fqn_)
        return super(Mapping, cls).update(id_, payload, dbsession)
