import uuid
from fastapi import (
    Depends,
    HTTPException,
    APIRouter,
    status
)
from sqlmodel import (
    Session,
    select
)
from ..models import get_session
from ..models.project import Project

router = APIRouter()

# TODO: setup router for the rest of the functions for project

@router.get("/projects", response_model=list[Project])
def get_all_projects(dbsession: Session = Depends(get_session)):
    projects = dbsession.exec(select(Project)).all()
    return projects

@router.post("/projects", response_model=Project)
def create_project(project: Project, dbsession: Session = Depends(get_session)):
    return Project.create(project, dbsession)

@router.get("/project/{project_id}", response_model=Project)
def get_project_by_id(project_id: uuid.UUID, dbsession: Session = Depends(get_session)):
    project = Project.get_by_id(project_id, dbsession)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project id {project_id} Not Found"
        )
    return project

@router.put("/project/{project_id}", response_model=Project)
def update_project(project_id: uuid.UUID, project_data: Project, dbsession: Session = Depends(get_session)):
    project = Project.update(project_id, project_data, dbsession)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project id {project_id} Not Found"
        )
    return project


def get_all():
    pass


def get_all_clients():
    pass


def get_by_code(cls, dbsession: Session, code: str):
    pass

"""
    @classmethod
    def get_all(
            cls,
            dbsession: Session,
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
            dbsession: Session,
            is_active: Optional[bool] = True
    ):
        projects = select(cls)
        if is_active is not None:
            projects.where(cls.is_active == is_active)
        projects = projects.order_by(cls.client_code.asc())
        results = dbsession.exec(projects).all()
        clients = {}
        for code, name in results:
            if not code in clients:
                clients[code] = {"client_code": code, "client_name": name}
        return list(clients.values())

    @classmethod
    def get_by_code(cls, dbsession: Session, code: str):
        return dbsession.exec(select(cls).where(cls.code == code)).one()
"""
