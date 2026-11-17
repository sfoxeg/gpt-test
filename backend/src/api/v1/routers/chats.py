from typing import Annotated
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user_id
from core.repositories import ChatsRepository
from core.schemas import SMessageIn

router = APIRouter()

@router.post("", status_code=201)
async def create_chat(other_user_id: int, user_id: Annotated[int, Depends(get_current_user_id)]):
    return await ChatsRepository.create(user_id, other_user_id)

@router.get("")
async def list_chats(user_id: Annotated[int, Depends(get_current_user_id)]):
    return await ChatsRepository.list_for_user(user_id)

@router.get("/{chat_id}/messages")
async def list_messages(chat_id: int, user_id: Annotated[int, Depends(get_current_user_id)]):
    return await ChatsRepository.messages(chat_id, user_id)

@router.post("/{chat_id}/messages", status_code=201)
async def send_message(chat_id: int, data: SMessageIn, user_id: Annotated[int, Depends(get_current_user_id)]):
    return await ChatsRepository.send_message(chat_id, user_id, data)
