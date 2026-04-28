from sqlmodel import (
    SQLModel,
    Session,
    create_engine
)
from .project import Project
from .location import Location
from .appliance import Appliance

engine = create_engine("sqlite:///./afd_local.db", echo=True)
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session



