from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from tortoise.contrib.fastapi import register_tortoise
from models import User_Pydantic, UserIn_Pydantic, User, InfoQueue_Pydantic, InfoQueueIn_Pydantic, InfoQueue
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from authentication import get_hashed_password, authenticate_user, create_access_token, get_current_user
from typing import Annotated, List
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
ACCESS_TOKEN_EXPIRE_MINUTES = 30
"""

TO DO:
1. Add queue get/post requests with token verification
2. Add dequeue post request with token verification

{
  "first_name": "test2",
  "last_name": "user2",
  "email": "user2@email.com",
  "password": "213435fsdfsdf"
}

{
  "first_name": "test_token",
  "last_name": "user_token",
  "email": "user_token@email.com",
  "password": "123456"
}
{
  "first_name": "test2_token",
  "last_name": "user2_token",
  "email": "user_token2@email.com",
  "password": "123456"
}
{
  "first_name": "test3_token",
  "last_name": "user3_token",
  "email": "user_token3@email.com",
  "password": "123456"
}
"""
register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

origins = [
    'http://localhost:5173',
    'http://localhost:5173/',
    'http://localhost:5173/registration',
    'http://localhost:5173/dashboard',
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Token(BaseModel):
    access_token: str


class Status(BaseModel):
    message: str


@app.get("/")
async def root():
    return {"message": "API"}


@app.post("/registration", response_model=Token)
async def create_user(user: UserIn_Pydantic):
    plain_password = user.password
    user.password = await get_hashed_password(user.password)
    user_obj = await User.create(**user.model_dump(exclude_unset=True))
    user = await authenticate_user(user_obj.email, plain_password)
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
    return {'access_token': access_token}


@app.get("/users/me/", response_model=User_Pydantic)
async def read_users_me(current_user: User_Pydantic = Depends(get_current_user)):
    return current_user


@app.post("/infoqueue/add_to_queue/", response_model=List[InfoQueue_Pydantic])
async def add_to_queue(remaining_inf: InfoQueueIn_Pydantic, current_user: User_Pydantic = Depends(get_current_user)):
    user_fname = current_user.first_name
    user_lname = current_user.last_name
    position = await InfoQueue.all().count() + 1
    task = remaining_inf.task_number
    subj = remaining_inf.subject_number
    await InfoQueue.create(position=position, first_name=user_fname, last_name=user_lname,
                           task_number=task, subject_number=subj)
    return await InfoQueue.all().order_by('task_number', 'created_at').filter(subject_number=subj).values()


@app.get('/infoqueue/get_queue/{subject}', response_model=List[InfoQueue_Pydantic])
async def get_queue(subject: int, current_user: User_Pydantic = Depends(get_current_user)):
    return await InfoQueue.all().order_by('task_number', 'created_at').filter(subject_number=subject).values()


@app.delete('/infoqueue/complete/{subject}', response_model=InfoQueue_Pydantic)
async def complete_queue(subject: int, current_user: User_Pydantic = Depends(get_current_user)):
    current_last_name = current_user.last_name
    end_queue = await InfoQueue.filter(last_name=current_last_name, subject_number=subject)
    if not end_queue:
        raise HTTPException(status_code=404, detail=f"{current_last_name} not found")
    return await InfoQueue.all().order_by('task_number', 'created_at').filter(subject_number=subject).values()
