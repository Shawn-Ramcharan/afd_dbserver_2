import uuid
from datetime import datetime, timezone
from sqlmodel import (
    Session,
    SQLModel,
    Field,
    Column,
    JSON
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
        return dbsession.get(cls, id)

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
    def create(cls, model: SQLModel, dbsession: Session):
        model._convert_data_types()
        model.set_creation_stamp(None)
        dbsession.add(model)
        dbsession.commit()
        dbsession.refresh(model)
        return model

    @classmethod
    def update(cls, id: uuid.UUID, model_data: SQLModel, dbsession: Session):
        model = cls.get_by_id(id, dbsession)
        model._convert_data_types()
        model_data._convert_data_types()
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

    def _convert_data_types(self):
        if isinstance(self.id, str):
            self.id = uuid.UUID(self.id)
        date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        if isinstance(self.creation_date, str):
            self.creation_date = datetime.strptime(
                self.creation_date,
                date_format
            )
        if isinstance(self.last_modified, str):
            self.last_modified = datetime.strptime(
                self.last_modified,
                date_format
            )

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
    attrs: dict | None = Field(sa_column=Column(JSON))
