from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.base_datos import Base


def fecha_actual_utc() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, default=fecha_actual_utc, nullable=False)

    ingredientes = relationship(
        "Ingrediente",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    recetas = relationship(
        "Receta",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
    calificaciones = relationship(
        "Calificacion",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
