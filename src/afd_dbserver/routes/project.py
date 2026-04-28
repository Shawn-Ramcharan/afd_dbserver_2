import uuid
from typing import Optional
from fastapi import (
    Depends,
    HTTPException,
    APIRouter,
    status
)
from sqlmodel import (
    Session,
)
from ..models import get_session
from ..models.project import Project

router = APIRouter()

@router.get("/projects", response_model=list[Project])
def get_all_project(
    is_active: Optional[bool] = None,
    client_code: Optional[str] = None,
    dbsession: Session = Depends(get_session)
):
    return Project.get_all(
        dbsession,
        client_code=client_code,
        is_active=is_active
    )

@router.post("/projects", response_model=Project)
def create_project(project: Project, dbsession: Session = Depends(get_session)):
    return Project.create(project, dbsession)

@router.get("/projects/{project_id}", response_model=Project)
def get_project_by_id(project_id: uuid.UUID, dbsession: Session = Depends(get_session)):
    project = Project.get_by_id(project_id, dbsession)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project id {project_id} Not Found"
        )
    return project

@router.put("/projects/{project_id}", response_model=Project)
def update_project(project_id: uuid.UUID, project_data: Project, dbsession: Session = Depends(get_session)):
    project = Project.update(project_id, project_data, dbsession)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project id {project_id} Not Found"
        )
    return project

@router.get("/projects/", response_model=Project)
def get_by_code(code: str, dbsession: Session = Depends(get_session)):
    project = Project.get_by_code(dbsession, code)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project code {code} Not Found"
        )
    return project

# NOTE: this route is different from
# will need to investigate later
@router.get("/projects_clients", response_model=list[dict])
def get_all_clients(is_active: Optional[bool] = None, dbsession: Session = Depends(get_session)):
    return Project.get_all_clients(
        dbsession,
        is_active=is_active
    )

@router.get("/projects/{id}/locations", response_model=Project)
def get_all_locations(dbsession: Session = Depends(get_session)):
    pass

@router.get("/projects/{id}/{attr}", response_model=Project)
def get_attrs(dbsession: Session = Depends(get_session)):
    pass

@router.get("/projects/{id}/slate", response_model=Project)
def get_next_take_from_slate(dbsession: Session = Depends(get_session)):
    pass
