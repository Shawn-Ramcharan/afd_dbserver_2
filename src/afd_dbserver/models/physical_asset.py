import enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy.exc import NoResultFound
from sqlalchemy import Enum as SqlaEnum
from sqlmodel import Session as DBSession
from sqlmodel import (
    SQLModel,
    Column,
    Field,
    Relationship,
    select
)
from .mixin import BaseMixin, AttrMixin
from .project import Project
from ..exc import NotFoundError

if TYPE_CHECKING:
    from .solver_setup import SolverSetup

class EPhysicalAssetType(enum.Enum):
    performer   = "performer"
    prop        = "prop"
    camera      = "camera"

class PhysicalAsset(BaseMixin, AttrMixin, SQLModel, table=True):
    """ 
    """
    __tablename__ = "physical_asset_t"
    code: str = Field(max_length=32, unique=True, nullable=False)
    name: str = Field(max_length=128)
    type_: EPhysicalAssetType = Field(
        sa_column=Column(SqlaEnum(EPhysicalAssetType,name='ephysicalassettype'))
    )
    subject_id: Optional[str] = Field(default=None, max_length=128, unique=True)
    solver_setups: "SolverSetup" = Relationship(back_populates="physical_asset")

    @classmethod
    def get_all(
        cls,
        dbsession: DBSession,
        type_: Optional[EPhysicalAssetType] = None,
        project_id: Optional[uuid.UUID] = None
    ):
        stmt = select(cls)
        if project_id is not None:
            stmt = select(SolverSetup).where(
                SolverSetup.project_id == project_id
            )
        if type_ is not None:
            stmt = stmt.where(cls.type_ == type_)
        return dbsession.exec(stmt).all()

    @classmethod
    def get_by_code(cls, dbsession: DBSession, code: str):
        try:
            return dbsession.exec(select(cls).where(cls.code == code)).one()
        except NoResultFound:
            raise NotFoundError(cls, code=code)
