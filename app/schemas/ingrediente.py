from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class IngredienteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120, examples=["Pechuga de pollo"])
    cantidad: float = Field(..., gt=0, examples=[500])
    unidad: str = Field(default="gramos", min_length=1, max_length=50, examples=["gramos"])

    @field_validator("nombre")
    @classmethod
    def validar_nombre_ingrediente(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre del ingrediente debe tener al menos 2 caracteres.")
        if limpio.isdigit():
            raise ValueError("El nombre del ingrediente no puede ser únicamente números.")
        return limpio

    @field_validator("unidad")
    @classmethod
    def validar_unidad(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("La unidad de medida no puede estar vacía.")
        return limpio


class IngredienteCrear(IngredienteBase):
    pass


class IngredienteActualizar(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=120)
    cantidad: Optional[float] = Field(None, gt=0)
    unidad: Optional[str] = Field(None, min_length=1, max_length=50)

    @field_validator("nombre")
    @classmethod
    def validar_nombre_opcional(cls, valor: Optional[str]) -> Optional[str]:
        if valor is not None:
            limpio = valor.strip()
            if len(limpio) < 2 or limpio.isdigit():
                raise ValueError("Nombre de ingrediente inválido.")
            return limpio
        return valor


class IngredienteRespuesta(IngredienteBase):
    id: int
    usuario_id: int
    fecha_registro: datetime

    model_config = ConfigDict(from_attributes=True)
