import os
from dotenv import load_dotenv
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager

from main import get_user
from models import User
