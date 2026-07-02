from datetime import datetime

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.engine import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    is_subscribed: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=False, server_default="0"
    )

    feedback: Mapped["UserFeedbackModel | None"] = relationship(
        "UserFeedbackModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    contacts: Mapped[list["UserContactModel"]] = relationship(
        "UserContactModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserFeedbackModel(Base):
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    feedback: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="feedback"
    )


class UserContactModel(Base):
    __tablename__ = "user_contacts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="contacts"
    )
