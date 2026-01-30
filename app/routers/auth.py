from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from ..config import ACCESS_TOKEN_EXPIRE_MINUTES
from ..dependencies import Oauth2PasswordRequestFormDep, SessionDep
from ..dependencies.users import authenticate_user, create_access_token
from ..models import Token, User

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/token")
async def login(form_data: Oauth2PasswordRequestFormDep, session: SessionDep):
    db_user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = authenticate_user(form_data.username, form_data.password, db_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
