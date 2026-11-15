from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.calificacion import CalificacionRespuesta


class ItemIngredienteReceta(BaseModel):
    nombre: str = Field(..., description="Nombre del ingrediente")
    cantidad: str = Field(..., description="Cantidad necesaria con su unidad")


class RecetaEstructuradaLLM(BaseModel):
    nombre_del_plato: str = Field(..., min_length=2)
    ingredientes: List[ItemIngredienteReceta] = Field(..., min_length=1)
    pasos_de_preparacion: List[str] = Field(..., min_length=1)
    tiempo_estimado: str = Field(..., min_length=2)
    nivel_de_dificultad: str = Field(..., min_length=2)


class SolicitudGenerarReceta(BaseModel):
    tipo_comida: Optional[str] = Field(
        default=None,
        max_length=80,
        description="Opcional: almuerzo, cena, desayuno, saludable, rápido, etc.",
        examples=["Almuerzo casero"],
    )


class RecetaRespuesta(BaseModel):
    id: int
    usuario_id: int
    nombre_del_plato: str
    ingredientes: List[ItemIngredienteReceta]
    pasos_de_preparacion: List[str]
    tiempo_estimado: str
    nivel_de_dificultad: str
    guardada: bool
    promedio_calificacion: Optional[float] = None
    mi_calificacion: Optional[int] = None
    calificaciones: List[CalificacionRespuesta] = []
    fecha_creacion: datetime
