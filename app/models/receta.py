from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.base_datos import Base


def fecha_actual_utc() -> datetime:
    return datetime.now(timezone.utc)


class Receta(Base):
    __tablename__ = "recetas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre_plato = Column(String(200), nullable=False)
    ingredientes_json = Column(Text, nullable=False)
    pasos_preparacion = Column(Text, nullable=False)
    tiempo_estimado = Column(String(80), nullable=False)
    nivel_dificultad = Column(String(50), nullable=False)
    guardada = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, default=fecha_actual_utc, nullable=False)

    usuario = relationship("Usuario", back_populates="recetas")
    calificaciones = relationship(
        "Calificacion",
        back_populates="receta",
        cascade="all, delete-orphan",
    )
