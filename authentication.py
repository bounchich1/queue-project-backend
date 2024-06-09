import os
import secrets
import string

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from dotenv import load_dotenv
from models import User, User_Pydantic


load_dotenv()
secret_key = os.getenv('SECRET')
algorithm = 'HS256'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class UserInDB(User):
    hashed_password: str


class TokenData(User):
    first_name: str
    last_name: str
    email: str


async def get_hashed_password(password):
    return pwd_context.hash(password)


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    return await User_Pydantic.from_queryset_single(User.get(email=email))


async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        return False
    if not await verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user(email=email)
    if user is None:
        raise credentials_exception
    return user


def generate_invitation_token(length=10):
    characters = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(characters) for _ in range(length))
    return token
