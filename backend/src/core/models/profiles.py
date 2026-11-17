from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.models.base import Base

class ProfilesOrm(Base):
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
    user: Mapped["UsersOrm"] = relationship(back_populates="profile")
    climbing: Mapped["ClimbingOrm"] = relationship(back_populates="profile", uselist=False, cascade="all, delete-orphan")

class ClimbingOrm(Base):
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
    profile: Mapped[ProfilesOrm] = relationship(back_populates="climbing")
