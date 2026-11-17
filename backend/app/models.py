from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    sex: Mapped[bool] = mapped_column(Boolean, default=False)
    date_of_birth: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="sender")

class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    goal: Mapped[int] = mapped_column(Integer, default=0)
    first_name: Mapped[str] = mapped_column(String(32), default="")
    last_name: Mapped[str] = mapped_column(String(32), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user: Mapped[User] = relationship(back_populates="profile")
    climbing: Mapped["Climbing"] = relationship(back_populates="profile", uselist=False, cascade="all, delete-orphan")

class Climbing(Base):
    __tablename__ = "climbing"
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    leading: Mapped[int] = mapped_column(Integer, default=0)
    where_leading: Mapped[int] = mapped_column(Integer, default=0)
    bouldering: Mapped[int] = mapped_column(Integer, default=0)
    where_bouldering: Mapped[int] = mapped_column(Integer, default=0)
    speed: Mapped[bool] = mapped_column(Boolean, default=False)
    alpinism: Mapped[bool] = mapped_column(Boolean, default=False)
    belay: Mapped[int] = mapped_column(Integer, default=0)
    belay_description: Mapped[str] = mapped_column(Text, default="")
    profile: Mapped[Profile] = relationship(back_populates="climbing")

class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    members: Mapped[list["ChatMember"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

class ChatMember(Base):
    __tablename__ = "chat_members"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    chat: Mapped[Chat] = relationship(back_populates="members")
    __table_args__ = (UniqueConstraint("chat_id", "user_id"),)

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    text: Mapped[str] = mapped_column(Text, default="")
    chat: Mapped[Chat] = relationship(back_populates="messages")
    sender: Mapped[User] = relationship(back_populates="messages")
