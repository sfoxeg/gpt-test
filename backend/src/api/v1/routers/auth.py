from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from core.repositories import AuthRepository
from core.schemas import SUserReg, SUserAuth

router = APIRouter()

@router.post("/register", status_code=201)
async def register_user(data: SUserReg):
    return await AuthRepository.register(data)

@router.post("/login")
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return await AuthRepository.login(SUserAuth(email=form.username, password=form.password))
