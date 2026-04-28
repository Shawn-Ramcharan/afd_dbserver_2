from typing import Optional
import uuid
from datetime import datetime, timezone
from sqlmodel import (
    Session,
    SQLModel,
    Field,
    JSON,
    select
)

def utcnow():
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)

class IdMixin(SQLModel):
    """ID
    """
    id: uuid.UUID = Field(
        # sa_type=UUID(as_uuid=True),
        primary_key=True,
        unique=True,
        nullable=False,
        default_factory=uuid.uuid4
    )

    @classmethod
    def get_by_id(cls, id: uuid.UUID, dbsession: Session):
        return dbsession.exec(select(cls).where(cls.id==id)).one()

class BaseMixin(IdMixin):
    """BaseMixin
    """
    created_by: str = Field(nullable=False)
    creation_date: datetime = Field(
        # sa_type=DateTime(timezone=True),
        default_factory=utcnow,
        nullable=False,
        # sa_column_kwargs={
        #     "server_default": utcnow
        # }
    )
    modified_by: str = Field(nullable=False)
    last_modified: datetime = Field(
        # sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={
            # "server_default": utcnow,
            "onupdate": utcnow
        }
    )

    @classmethod
    def create(cls, payload: SQLModel, dbsession: Session):
        model = cls.model_validate(payload)
        model.set_creation_stamp(None)
        dbsession.add(model)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    @classmethod
    def update(cls, id: uuid.UUID, payload: SQLModel, dbsession: Session):
        model = cls.get_by_id(id, dbsession)
        model_data = cls.model_validate(payload)
        if not model:
            return None
        print("*"*50)
        print(model_data.model_dump().keys())
        print("*"*50)
        for field, value in model_data.model_dump().items():
            setattr(model, field, value)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    def set_creation_stamp(self, request):
        pass
        # track the creating user
        # self.created_by = request.authenticated_userid
        # self.modified_by = request.authenticated_userid

    def update_stamp(self, request):
        pass
        # track the modifying user
        # self.modified_by = request.authenticated_userid

class AttrMixin(SQLModel):
    """Extra Attributes to add in database.
    """
    attrs: Optional[dict] = Field(default=None, sa_type=JSON)
