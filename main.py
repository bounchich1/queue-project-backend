from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from models import User_Pydantic, UserIn_Pydantic, User
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from authentication import get_hashed_password

app = FastAPI()

"""
{
  "first_name": "test2",
  "last_name": "user2",
  "email": "user2@email.com",
  "password": "213435fsdfsdf"
}
"""


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


register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
