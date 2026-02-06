from fastapi import APIRouter, Depends
from sqlmodel import select

from ..db.db import SessionDep
from ..auth.users import oauth2_scheme
from ..auth.users import CurrentUser
from ..models import User, UserBase

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(oauth2_scheme)],
)


@router.get("/me", response_model=UserBase)
async def read_users_me(current_user: CurrentUser):
    return current_user


@router.get("/", response_model=list[UserBase])
def read_users(session: SessionDep):
    users = session.exec(select(User)).all()
    return users


@router.get("/{user_name}", response_model=UserBase)
def read_user(user_name: str, session: SessionDep):
    db_user = session.exec(select(User).where(User.username == user_name)).first()
    return db_user


@router.post("/", response_model=UserBase)
def create_user(user: UserBase, session: SessionDep):
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
