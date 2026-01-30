from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, SQLModel, create_engine

from ..config import SQLITE_FILE_NAME

sqlite_url = f"sqlite:///..{SQLITE_FILE_NAME}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SessionDep = Annotated[Session, Depends(get_session)]
AuthDep = Annotated[str, Depends(oauth2_scheme)]
Oauth2PasswordRequestFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]
