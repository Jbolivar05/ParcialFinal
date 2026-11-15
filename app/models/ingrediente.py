from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.base_datos import Base


def fecha_actual_utc() -> datetime:
    return datetime.now(timezone.utc)


class Ingrediente(Base):
    __tablename__ = "ingredientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre = Column(String(120), nullable=False)
    cantidad = Column(Float, nullable=False)
    unidad = Column(String(50), nullable=False, default="unidades")
    fecha_registro = Column(DateTime, default=fecha_actual_utc, nullable=False)

    usuario = relationship("Usuario", back_populates="ingredientes")
