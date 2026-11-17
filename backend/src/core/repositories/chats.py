from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from core.database import new_session
from core.models import UsersOrm, ChatsOrm, ChatMembersOrm, MessagesOrm
from core.schemas import SMessageIn, SMessageOut

class ChatsRepository:
    @classmethod
    async def create(cls, user_id: int, other_user_id: int) -> dict:
        if user_id == other_user_id:
            raise HTTPException(400, "Cannot create a chat with yourself")
        async with new_session() as session:
            other = await session.get(UsersOrm, other_user_id)
            if not other or not other.is_active:
                raise HTTPException(404, "User not found")
            existing = await session.scalar(
                select(ChatsOrm).join(ChatMembersOrm, ChatMembersOrm.chat_id == ChatsOrm.id)
                .where(ChatMembersOrm.user_id == user_id)
                .where(ChatsOrm.id.in_(select(ChatMembersOrm.chat_id).where(ChatMembersOrm.user_id == other_user_id)))
                .options(selectinload(ChatsOrm.members))
            )
            if existing and len(existing.members) == 2:
                return {"id": existing.id}
            chat = ChatsOrm(members=[ChatMembersOrm(user_id=user_id), ChatMembersOrm(user_id=other.id)])
            session.add(chat)
            await session.flush()
            chat_id = chat.id
            await session.commit()
            return {"id": chat_id}

    @classmethod
    async def list_for_user(cls, user_id: int) -> list[dict]:
        async with new_session() as session:
            result = await session.execute(
                select(ChatsOrm).join(ChatMembersOrm).where(ChatMembersOrm.user_id == user_id)
                .options(selectinload(ChatsOrm.members))
            )
            return [{"id": c.id, "members": [m.user_id for m in c.members]} for c in result.scalars().unique().all()]

    @classmethod
    async def _ensure_member(cls, session, chat_id: int, user_id: int) -> None:
        member = await session.scalar(select(ChatMembersOrm.id).where(
            ChatMembersOrm.chat_id == chat_id, ChatMembersOrm.user_id == user_id
        ))
        if member is None:
            raise HTTPException(404, "Chat not found")

    @classmethod
    async def messages(cls, chat_id: int, user_id: int) -> list[SMessageOut]:
        async with new_session() as session:
            await cls._ensure_member(session, chat_id, user_id)
            await session.execute(update(MessagesOrm).where(
                MessagesOrm.chat_id == chat_id, MessagesOrm.sender_id != user_id,
                MessagesOrm.is_read.is_(False)
            ).values(is_read=True))
            result = await session.execute(select(MessagesOrm).where(
                MessagesOrm.chat_id == chat_id
            ).order_by(MessagesOrm.created_at, MessagesOrm.id))
            messages = [SMessageOut.model_validate(m) for m in result.scalars().all()]
            await session.commit()
            return messages

    @classmethod
    async def send_message(cls, chat_id: int, user_id: int, data: SMessageIn) -> SMessageOut:
        async with new_session() as session:
            await cls._ensure_member(session, chat_id, user_id)
            message = MessagesOrm(chat_id=chat_id, sender_id=user_id, text=data.text.strip())
            if not message.text:
                raise HTTPException(422, "Message cannot be empty")
            session.add(message)
            await session.flush()
            await session.refresh(message)
            response = SMessageOut.model_validate(message)
            await session.commit()
            return response
