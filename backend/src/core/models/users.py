from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.models.base import Base
from core.models.mixins import IdPKMixin, CreatedAtMixin

class UsersOrm(IdPKMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    sex: Mapped[bool] = mapped_column(Boolean, default=False)
    date_of_birth: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    profile: Mapped["ProfilesOrm"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    messages: Mapped[list["MessagesOrm"]] = relationship(back_populates="sender")
