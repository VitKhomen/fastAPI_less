from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.engine import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
