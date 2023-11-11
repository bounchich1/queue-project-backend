import os
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi_users.authentication import CookieTransport, JWTStrategy, AuthenticationBackend
from dotenv import load_dotenv

load_dotenv()
secret_key = os.getenv('SECRET')
cookie_transport = CookieTransport(cookie_name='test', cookie_max_age=3600)

pwd_context = CryptContext(schemes=['argon2', 'bcrypt'], deprecated='auto')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_hashed_password(password):
    return pwd_context.hash(password)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=secret_key, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name='jwt',
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)
