from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.models.base import Base
from core.models.mixins import IdPKMixin, CreatedAtMixin

class ChatsOrm(IdPKMixin, CreatedAtMixin, Base):
    __tablename__ = "chats"
    name: Mapped[str] = mapped_column(String(255), default="")
    members: Mapped[list["ChatMembersOrm"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    messages: Mapped[list["MessagesOrm"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

class ChatMembersOrm(IdPKMixin, Base):
    __tablename__ = "chat_members"
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    chat: Mapped[ChatsOrm] = relationship(back_populates="members")
    __table_args__ = (UniqueConstraint("chat_id", "user_id"),)

class MessagesOrm(IdPKMixin, CreatedAtMixin, Base):
    __tablename__ = "messages"
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    text: Mapped[str] = mapped_column(Text, default="")
    chat: Mapped[ChatsOrm] = relationship(back_populates="messages")
    sender: Mapped["UsersOrm"] = relationship(back_populates="messages")
