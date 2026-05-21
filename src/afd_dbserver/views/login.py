from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/login/test")
def read_root(request: Request):
    body = {
        "authenticated_user_id": "shawn"
    }
    return {
        "data": body
    }
