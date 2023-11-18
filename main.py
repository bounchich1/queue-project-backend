from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from tortoise.contrib.fastapi import register_tortoise
from models import User_Pydantic, UserIn_Pydantic, User
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from authentication import get_hashed_password, authenticate_user, create_access_token, get_current_user
from typing import Annotated
from datetime import datetime, timedelta

app = FastAPI()
ACCESS_TOKEN_EXPIRE_MINUTES = 30
"""
{
  "first_name": "test2",
  "last_name": "user2",
  "email": "user2@email.com",
  "password": "213435fsdfsdf"
}
"""


class Token(BaseModel):
    access_token: str
    token_type: str


class Status(BaseModel):
    message: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/registration", response_model=User_Pydantic)
async def create_user(user: UserIn_Pydantic):
    user.password = get_hashed_password(user.password)
    user_obj = await User.create(**user.model_dump(exclude_unset=True))
    return await User_Pydantic.from_tortoise_orm(user_obj)


@app.get("/user/{user_id}", response_model=User_Pydantic)
async def get_user(user_id: int):
    return await User_Pydantic.from_queryset_single(User.get(id=user_id))


@app.delete("/user/{user_id}", response_model=Status)
async def delete_user(user_id: int):
    deleted_count = await User.filter(id=user_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return Status(message=f"Deleted user {user_id}")


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User_Pydantic)
async def read_users_me(current_user: User_Pydantic = Depends(get_current_user)):
    return current_user


register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
