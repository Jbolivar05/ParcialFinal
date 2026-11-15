from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioCrear(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["María Gómez"])
    email: EmailStr = Field(..., examples=["maria@unisimon.edu.co"])
    password: str = Field(..., min_length=6, max_length=100, examples=["ClaveSegura123"])

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        limpio = valor.strip()
        if len(limpio) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres válidos.")
        return limpio


class UsuarioLogin(BaseModel):
    email: EmailStr = Field(..., examples=["maria@unisimon.edu.co"])
    password: str = Field(..., min_length=1, examples=["ClaveSegura123"])


class UsuarioRespuesta(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioRespuesta
