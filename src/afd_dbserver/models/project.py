from typing import TYPE_CHECKING, Optional
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session as DBSession
from sqlmodel import (
    SQLModel,
    Field,
    Relationship,
    select
)
from .mixin import BaseMixin, AttrMixin
from .resource_mixin import ResourceMixin
from ..exc import NotFoundError

if TYPE_CHECKING:
    from .take import Take
    from .take_select import TakeSelect
    from .virtual_asset import VirtualAsset
    from .session import Session
from .resource import Resource, ResourceAssoc

class Project(BaseMixin, AttrMixin, ResourceMixin, SQLModel, table=True):
    """Project Table.
    """
    __tablename__ = "project_t"
    code: str = Field(max_length=32, unique=True, nullable=False)
    name: Optional[str] = Field(max_length=128)
    client_code: Optional[str] = Field(max_length=32)
    client_name: Optional[str] = Field(max_length=128)
    description: Optional[str] = Field()
    root_folder: Optional[str] = Field(max_length=512)
    is_active: Optional[bool] = Field(default=True)
    virtual_assets: "VirtualAsset" = Relationship()# order_by="VirtualAsset.code.asc()")
    sessions: list["Session"] = Relationship()
    takes: list["Take"] = Relationship()# order_by="Take.creation_date.desc()")
    take_selects: list["TakeSelect"] = Relationship()#"TakeSelect")
    take_select_lists: list["TakeSelectList"] = Relationship()# order_by="TakeSelectList.last_modified.desc()")
    resources: list[Resource] = Relationship(
        link_model=ResourceAssoc,
        back_populates="project"
    )

    @classmethod
    def get_all(
            cls,
            dbsession: DBSession,
            client_code: Optional[str] = None,
            is_active: Optional[bool] = True
    ):
        projects = select(cls)
        if is_active is not None:
            projects = projects.where(cls.is_active == is_active)
        if client_code is not None:
            projects = projects.where(cls.client_code == client_code)
        projects = projects.order_by(cls.code.asc())
        return dbsession.exec(projects).all()

    @classmethod
    def get_all_clients(
            cls,
            dbsession: DBSession,
            is_active: Optional[bool] = True
    ):
        projects = select(cls)
        if is_active is not None:
            projects.where(cls.is_active == is_active)
        projects = projects.order_by(cls.client_code.asc())
        results = dbsession.exec(projects).all()
        clients = {}
        for project_ in results:
            code = project_.client_code
            name = project_.client_name
            if not code in clients:
                clients[code] = {"client_code": code, "client_name": name}
        return list(clients.values())

    @classmethod
    def get_by_code(cls, dbsession: DBSession, code: str):
        try:
            return dbsession.exec(select(cls).where(cls.code == code)).one()
        except NoResultFound:
            raise NotFoundError(cls, code=code)

