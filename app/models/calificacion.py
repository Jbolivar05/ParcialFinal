from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.base_datos import Base


def fecha_actual_utc() -> datetime:
    return datetime.now(timezone.utc)


class Calificacion(Base):
    __tablename__ = "calificaciones"

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(
        Integer,
        ForeignKey("recetas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(String(500), nullable=True)
    fecha_calificacion = Column(DateTime, default=fecha_actual_utc, nullable=False)

    receta = relationship("Receta", back_populates="calificaciones")
    usuario = relationship("Usuario", back_populates="calificaciones")
