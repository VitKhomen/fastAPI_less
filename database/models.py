from datetime import datetime

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.engine import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)

    feedback: Mapped["UserFeedbackModel | None"] = relationship(
        "UserFeedbackModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


class UserFeedbackModel(Base):
    __tablename__ = "user_feedback"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    feedback: Mapped[str | None] = mapped_column(String(256), nullable=True)

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="feedback"
    )
