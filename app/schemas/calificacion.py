from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CalificacionCrear(BaseModel):
    puntuacion: int = Field(
        ...,
        ge=1,
        le=5,
        description="Calificación de la receta en escala de 1 a 5 estrellas",
        examples=[5],
    )
    comentario: Optional[str] = Field(
        default=None,
        max_length=500,
        examples=["Excelente receta, muy fácil de preparar con lo que tenía en casa."],
    )


class CalificacionRespuesta(BaseModel):
    id: int
    receta_id: int
    usuario_id: int
    puntuacion: int
    comentario: Optional[str] = None
    fecha_calificacion: datetime

    model_config = ConfigDict(from_attributes=True)
