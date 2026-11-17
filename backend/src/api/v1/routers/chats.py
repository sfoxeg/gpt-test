from typing import Annotated
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user_id
from core.repositories import ChatsRepository
from core.schemas import SMessageIn
from core.realtime import broadcast_chat, manager

router = APIRouter()

@router.post("", status_code=201)
async def create_chat(other_user_id: int, user_id: Annotated[int, Depends(get_current_user_id)]):
    return await ChatsRepository.create(user_id, other_user_id)

@router.get("")
async def list_chats(user_id: Annotated[int, Depends(get_current_user_id)]):
    return await ChatsRepository.list_for_user(user_id)

@router.get("/{chat_id}/messages")
async def list_messages(chat_id: int, user_id: Annotated[int, Depends(get_current_user_id)]):
    messages = await ChatsRepository.messages(chat_id, user_id)
    await broadcast_chat(chat_id, user_id, {"type": "messages.read", "chat_id": chat_id, "user_id": user_id})
    return messages

@router.get("/{chat_id}/presence")
async def chat_presence(chat_id: int, user_id: Annotated[int, Depends(get_current_user_id)]):
    from core.database import new_session
    from core.models import ChatMembersOrm
    from sqlalchemy import select
    async with new_session() as session:
        members = await session.scalars(select(ChatMembersOrm.user_id).where(ChatMembersOrm.chat_id == chat_id))
        ids = set(members.all())
    if user_id not in ids:
        from fastapi import HTTPException
        raise HTTPException(404, "Chat not found")
    return {str(uid): await manager.online(uid) for uid in ids if uid != user_id}

@router.post("/{chat_id}/messages", status_code=201)
async def send_message(chat_id: int, data: SMessageIn, user_id: Annotated[int, Depends(get_current_user_id)]):
    message = await ChatsRepository.send_message(chat_id, user_id, data)
    await broadcast_chat(chat_id, user_id, {"type": "message", "message": message.model_dump(mode="json")})
    return message
