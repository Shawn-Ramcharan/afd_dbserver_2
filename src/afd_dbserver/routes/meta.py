from fastapi import (
    APIRouter,
    Request
)

from ..models.mixin import get_object_meta

router = APIRouter(
    prefix="/meta",
    tags=["Meta"]
)

@router.get("")
def get(request: Request):
    return {
        # "request": request,
        "status": "ok",
        "code": 200,
        "data": get_object_meta()
    }
