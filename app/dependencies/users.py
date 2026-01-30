import datetime

import jwt
from fastapi import Depends, HTTPException, status
from pwdlib import PasswordHash
from sqlmodel import select
from typing_extensions import Annotated

from ..config import ALGORITHM, SECRET_KEY
from ..dependencies import AuthDep, SessionDep
from ..models import TokenData, User

password_hash = PasswordHash.recommended()


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=15
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: AuthDep, session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = session.exec(
        select(User).where(User.username == token_data.username)
    ).first()
    if user is None:
        raise credentials_exception
    return user


def authenticate_user(username: str, password: str, user: User):
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


UserDep = Annotated[User, Depends(get_current_user)]
