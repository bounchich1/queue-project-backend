from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from models import User_Pydantic, UserIn_Pydantic, User
from pydantic import BaseModel
from starlette.exceptions import HTTPException

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/users", response_model=User_Pydantic)
async def create_user(user: UserIn_Pydantic):
    user_obj = await User.create(**user.model_dump(exclude_unset=True))
    return await User_Pydantic.from_tortoise_orm(user_obj)


@app.get("/user/{user_id}", response_model=User_Pydantic)
async def get_user(user_id: int):
    return await User_Pydantic.from_queryset_single(User.get(id=user_id))


register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
