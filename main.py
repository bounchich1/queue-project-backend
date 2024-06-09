import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from tortoise.contrib.fastapi import register_tortoise
from models import User_Pydantic, UserIn_Pydantic, User, InfoQueue_Pydantic, InfoQueueIn_Pydantic, InfoQueue, \
    Subjects_Pydantic, SubjectsIn_Pydantic, Subjects, Tokens_Pydantic, Tokens, Subscription, \
    Subscription_Pydantic, SubscriptionIn_Pydantic, UserOut_Pydantic, Groups, Groups_Pydantic, GroupsIn_Pydantic, \
    SubjectsUpd_Pydantic
from pydantic import BaseModel
from fastapi_mail import FastMail, ConnectionConfig
from starlette.exceptions import HTTPException
from dotenv import load_dotenv
from authentication import get_hashed_password, authenticate_user, create_access_token, get_current_user, \
    generate_invitation_token
from typing import Annotated, List
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
username = os.getenv('SECRET_EMAIL')
password = os.getenv('SECRET_PASSWORD')
app = FastAPI()
ACCESS_TOKEN_EXPIRE_MINUTES = 30

conf = ConnectionConfig(
    MAIL_USERNAME=username,
    MAIL_PASSWORD=password,
    MAIL_FROM=username,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Team W8Whiz",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
fast_mail = FastMail(conf)
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
    'http://localhost:4173/',
    'http://localhost:4173/registration',
    'http://localhost:4173/dashboard',
    'http://localhost:4173',
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
    """
    verification_token_expires = timedelta(minutes=10)
    verification_token = create_access_token(data={'sub': user.email}, expires_delta=verification_token_expires)
    await send_verification_email(user.email, verification_token)
    """
    return {"access_token": access_token, "token_type": "bearer"}


"""
async def send_verification_email(email: str, token: str):
    message = MessageSchema(subject="Verify your email", recipients=[email],
                            body=f"Click the link below to verify your email token: /{token}",
                            subtype=MessageType.html)
    await fast_mail.send_message(message)
"""


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
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
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


@app.get("/users/me/", response_model=UserOut_Pydantic)
async def read_users_me(current_user: User_Pydantic = Depends(get_current_user)):
    return current_user


@app.post("/infoqueue/add_to_queue/", response_model=List[InfoQueue_Pydantic])
async def add_to_queue(remaining_inf: InfoQueueIn_Pydantic, current_user: User_Pydantic = Depends(get_current_user)):
    current_id = current_user.id
    subj = remaining_inf.subject_number
    current_group = current_user.group_id
    position = 1
    existing_entry = await InfoQueue.filter(user_id=current_id, subject_number=subj, group_id=current_group).first()
    if existing_entry:
        raise HTTPException(status_code=400, detail='User is already in queue')
    task = remaining_inf.task_number
    user_fname = current_user.first_name
    user_lname = current_user.last_name
    await InfoQueue.create(user_id=current_id, position=position, group_id=current_group, first_name=user_fname,
                           last_name=user_lname,
                           task_number=task, subject_number=subj)
    return await InfoQueue.all().order_by('created_at',
                                          'task_number').filter(subject_number=subj,
                                                                group_id=current_group).only('position',
                                                                                             'task_number',
                                                                                             'first_name',
                                                                                             'last_name').values()


@app.get('/infoqueue/get_queue/{subject}', response_model=List[InfoQueue_Pydantic])
async def get_queue(subject: str, current_user: User_Pydantic = Depends(get_current_user)):
    return await InfoQueue.all().order_by('created_at',
                                          'task_number'). \
        filter(subject_number=subject,
               group_id=current_user.group_id).only('position',
                                                    'task_number',
                                                    'first_name',
                                                    'last_name').values()


@app.delete('/infoqueue/complete/{subject}', response_model=List[InfoQueue_Pydantic])
async def complete_queue(subject: str, current_user: User_Pydantic = Depends(get_current_user)):
    current_last_name = current_user.last_name
    current_id = current_user.id
    end_queue = await InfoQueue.filter(user_id=current_id,
                                       subject_number=subject).delete()
    if not end_queue:
        raise HTTPException(status_code=404, detail=f"{current_last_name} not found")
    return await InfoQueue.all().order_by('position'). \
        filter(subject_number=subject,
               group_id=current_user.group_id).only('position',
                                                    'task_number',
                                                    'first_name',
                                                    'last_name').values()


@app.get('/infoqueue/get_subjects/', response_model=List[Subjects_Pydantic])
async def get_subjects(current_user: User_Pydantic = Depends(get_current_user)):
    return await Subjects.all().order_by('subject_full_name'). \
        filter(group_id=current_user.group_id).only('subject_full_name',
                                                    'subject_short_name').values()


@app.post('/infoqueue/add_new_subjects/', response_model=List[Subjects_Pydantic])
async def add_new_subjects(subjects_info: SubjectsIn_Pydantic,
                           current_user: User_Pydantic = Depends(get_current_user)):
    current_group = current_user.group_id
    subjects_full_name = subjects_info.subject_full_name
    subjects_short_name = subjects_info.subject_short_name
    existing_subject = await Subjects.filter(group_id=current_group, subject_full_name=subjects_full_name,
                                             subject_short_name=subjects_short_name)
    if existing_subject:
        raise HTTPException(status_code=400, detail=f'{subjects_full_name} already exists')
    else:
        await Subjects.create(group_id=current_group, subject_full_name=subjects_full_name,
                              subject_short_name=subjects_short_name)
    return await Subjects.all().filter(group_id=current_group).only('subject_full_name',
                                                                    'subject_short_name').values()


@app.post('/infoqueue/update_subject', response_model=Status)
async def update_subject(subject_upd: SubjectsUpd_Pydantic, current_user: User_Pydantic = Depends(get_current_user)):
    current_subject = await Subjects.get(id=subject_upd.id)
    current_subject.subject_short_name = subject_upd.subject_short_name
    current_subject.subject_full_name = subject_upd.subject_full_name
    await current_subject.save()
    return Status(message='Предмет был успешно обновлен')


@app.get('/user/subscription_plan/', response_model=Subscription_Pydantic)
async def get_subscription_plan(current_user: User_Pydantic = Depends(get_current_user)):
    subscription_plan = await Subscription_Pydantic.from_queryset_single(Subscription.get(owner_id=current_user.id))
    if not subscription_plan:
        raise HTTPException(status_code=400, detail=f'Подписка не найдена')
    return subscription_plan


@app.get('/user/generate_invitation_token/', response_model=Tokens_Pydantic)
async def create_invitation_token(current_user: User_Pydantic = Depends(get_current_user)):
    subscription_plan = await Subscription_Pydantic.from_queryset_single(Subscription.get(owner_id=current_user.id))
    new_token = generate_invitation_token()
    await Tokens.create(group_id=subscription_plan.group_id,
                        remaining_activations=subscription_plan.group_population,
                        token=new_token, owner_id=subscription_plan.owner_id, expires=subscription_plan.expires)
    return await Tokens_Pydantic.from_queryset_single(Tokens.get(group_id=subscription_plan.group_id))


@app.get('/user/get_invitation_token/', response_model=Tokens_Pydantic)
async def get_invitation_token(current_user: User_Pydantic = Depends(get_current_user)):
    return await Tokens_Pydantic.from_queryset_single(Tokens.get(group_id=current_user.group_id))


@app.post('/user/activate_subscription/', response_model=Status)
async def activate_subscription(subscription_info: SubscriptionIn_Pydantic, group_info: GroupsIn_Pydantic,
                                current_user: User_Pydantic = Depends(get_current_user)):
    if current_user.group_id is None:
        new_group = await Groups.create(group_number=group_info.group_number)
        user = await User.get(id=current_user.id)
        user.group_id = new_group.group_id
        await user.save()
    existing_subscription = await Subscription.filter(owner_id=current_user.group_id)
    if existing_subscription:
        raise HTTPException(status_code=400, detail='Ваша подписка уже активна')
    current_datetime = datetime.now()
    expires = current_datetime + relativedelta(months=+subscription_info.months)
    user = await User.get(id=current_user.id)
    await Subscription.create(tier=subscription_info.tier, owner_id=current_user.id,
                              group_population=subscription_info.group_population,
                              expires=expires, created_at=current_datetime, group_id=user.group_id,
                              months=subscription_info.months)
    user = await User.get(id=current_user.id)
    user.role = 'moderator'
    user.subscription_expires = expires
    await user.save()
    return Status(message='Ваша подписка успешно активирована')


@app.post('/user/enter_invitation_token/{token}', response_model=Status)
async def enter_invitation_token(token: str, current_user: User_Pydantic = Depends(get_current_user)):
    token_info = await Tokens.get(token=token)
    current_time = datetime.now()
    user = await User.get(id=current_user.id)
    if token_info.remaining_activations == 0:
        raise HTTPException(status_code=400, detail='Превышен лимит активаций!')
    else:
        if current_user.group_id is None:
            user.group_id = token_info.group_id
            user.subscription_expires = token_info.expires
            await user.save()
        token_info.remaining_activations -= 1
        await token_info.save()

    return Status(message=f'Вы успешно добавлены в группу {token_info.group_id}, ваша подписка активна')


@app.post('/groups/set_group_name/', response_model=Groups_Pydantic)
async def set_group_number(group_info: GroupsIn_Pydantic, current_user: User_Pydantic = Depends(get_current_user)):
    new_group_number = group_info.group_number
    new_group = await Groups.create(group_number=new_group_number)
    if current_user.group_id is None:
        user = await User.get(id=current_user.id)
        user.group_id = new_group.group_id
        await user.save()
    return await Groups.get(group_id=new_group.group_id)


@app.get('/users/list_of_users/', response_model=List[User_Pydantic])
async def get_list_of_users(current_user: User_Pydantic = Depends(get_current_user)):
    return await User.filter(group_id=current_user.group_id).only('first_name', 'last_name').values()


@app.get('/groups/get_group_number/', response_model=Groups_Pydantic)
async def get_group_number(current_user: User_Pydantic = Depends(get_current_user)):
    return await Groups.get(group_id=current_user.group_id)
