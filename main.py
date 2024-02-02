import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from tortoise.contrib.fastapi import register_tortoise
from models import User_Pydantic, UserIn_Pydantic, User, InfoQueue_Pydantic, InfoQueueIn_Pydantic, InfoQueue
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from authentication import get_hashed_password, authenticate_user, create_access_token, get_current_user
from typing import Annotated, List
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mail import FastMail, ConnectionConfig

app = FastAPI()
ACCESS_TOKEN_EXPIRE_MINUTES = 30
"""
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

load_dotenv()

mail_username = os.getenv('MAIL_USERNAME')
mail_password = os.getenv('MAIL_PASSWORD')
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

conf = ConnectionConfig(
    MAIL_USERNAME=mail_username,
    MAIL_PASSWORD=mail_password,
    MAIL_FROM='kakoytochelick465@gmail.com',
    MAIL_PORT=587,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fm = FastMail(conf)


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
    position = current_user.id
    subj = remaining_inf.subject_number
    existing_enrty = await InfoQueue.filter(position=position, subject_number=subj).first()
    if existing_enrty:
        raise HTTPException(status_code=400, detail='User is already in queue')
    task = remaining_inf.task_number
    user_fname = current_user.first_name
    user_lname = current_user.last_name
    await InfoQueue.create(position=position, first_name=user_fname, last_name=user_lname,
                           task_number=task, subject_number=subj)
    return await InfoQueue.all().order_by('task_number', 'created_at').filter(subject_number=subj).values()


@app.get('/infoqueue/get_queue/{subject}', response_model=List[InfoQueue_Pydantic])
async def get_queue(subject: int, current_user: User_Pydantic = Depends(get_current_user)):
    return await InfoQueue.all().order_by('task_number', 'created_at').filter(subject_number=subject).values()


@app.delete('/infoqueue/complete/{subject}', response_model=List[InfoQueue_Pydantic])
async def complete_queue(subject: int, current_user: User_Pydantic = Depends(get_current_user)):
    current_last_name = current_user.last_name
    current_id = current_user.id
    end_queue = await InfoQueue.filter(position=current_id,
                                       subject_number=subject).delete()
    if not end_queue:
        raise HTTPException(status_code=404, detail=f"{current_last_name} not found")
    return await InfoQueue.all().order_by('task_number', 'created_at').filter(subject_number=subject).values()


"""
DOES NOT ALLOW TO PROCEED HTTP REQUESTS WHILE WEBSOCKET CONNECTION IS OPENED

TODO: implement a websocket somewhere in the future..

connected_users = set()

@app.websocket('/ws/{subject}')
async def websocket_endpoint(websocket: WebSocket, subject: int):
    current_user = await read_users_me()
    if not current_user:
        raise HTTPException(status_code=400, detail='You are not permitted to connect')
    await websocket.accept()
    connected_users.add(websocket)

    try:
        initial_queue_data = await get_queue_1(subject)
        await websocket.send_json(initial_queue_data)

        while True:
            update_queue_data = await get_queue_1(subject)
            await websocket.send_json(update_queue_data)

    except Exception as error:
        print(f'Websocket connection lost {error}')
        connected_users.remove(websocket)


async def get_queue_1(subject: int) -> List:
    queue_data = await InfoQueue.all().order_by('task_number', 'created_at').filter(subject_number=subject).values()
    serialized_queue_data = []
    for item in queue_data:
        serialized_item = {
            'position': item['position'],
            'first_name': item['first_name'],
            'last_name': item['last_name'],
            'task_number': item['task_number'],
            'subject_number': item['subject_number'],
            'created_at': item['created_at'].isoformat(),
            'modified_at': item['modified_at'].isoformat() if item['modified_at'] else None
        }
        serialized_queue_data.append(serialized_item)

    return serialized_queue_data



    FRONTEND SOLUTION
    
    
    connectWebSocket(queueNumber){
    this.socket = new WebSocket(`ws://127.0.0.1:8000/ws/${queueNumber}`);

    this.socket.onopen = () => {
      console.log('WebSocket connection is opened');
    };
    this.socket.onmessage = (event) => {
      const receivedData = JSON.parse(event.data);
      this.jsonDataList = receivedData;
      console.log(this.jsonDataList)  
    };
    this.socket.onerror = (error) => {
      console.error('WebSocket error', error);
    };
  },
  
  
    beforeUnmount() {
    if (this.socket != null) {
      this.socket.close();
    }
  },
"""
