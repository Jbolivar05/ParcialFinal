from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.base_datos import obtener_bd
from app.models import Ingrediente, Usuario
from app.schemas import (
    IngredienteActualizar,
    IngredienteCrear,
    IngredienteRespuesta,
)
from app.seguridad import obtener_usuario_actual

enrutador = APIRouter(prefix="/api/ingredientes", tags=["Inventario de Ingredientes"])


@enrutador.get(
    "",
    response_model=List[IngredienteRespuesta],
    summary="Listar ingredientes del inventario personal",
    description="Obtiene todos los ingredientes registrados en casa por el usuario autenticado.",
)
def listar_ingredientes(
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    elementos = (
        bd.query(Ingrediente)
        .filter(Ingrediente.usuario_id == usuario_actual.id)
        .order_by(Ingrediente.fecha_registro.desc())
        .all()
    )
    return elementos


@enrutador.post(
    "",
    response_model=IngredienteRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar ingrediente al inventario",
    description="Registra un nuevo ingrediente con su cantidad y unidad en el inventario personal.",
)
def crear_ingrediente(
    datos_ingrediente: IngredienteCrear,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    nuevo_elemento = Ingrediente(
        usuario_id=usuario_actual.id,
        nombre=datos_ingrediente.nombre,
        cantidad=datos_ingrediente.cantidad,
        unidad=datos_ingrediente.unidad,
    )
    bd.add(nuevo_elemento)
    bd.commit()
    bd.refresh(nuevo_elemento)
    return nuevo_elemento


@enrutador.get(
    "/{ingrediente_id}",
    response_model=IngredienteRespuesta,
    summary="Obtener detalle de un ingrediente",
)
def obtener_ingrediente(
    ingrediente_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    elemento = (
        bd.query(Ingrediente)
        .filter(
            Ingrediente.id == ingrediente_id,
            Ingrediente.usuario_id == usuario_actual.id,
        )
        .first()
    )
    if not elemento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingrediente no encontrado en tu inventario.",
        )
    return elemento


@enrutador.put(
    "/{ingrediente_id}",
    response_model=IngredienteRespuesta,
    summary="Actualizar un ingrediente del inventario",
    description="Modifica el nombre, cantidad o unidad de un ingrediente existente.",
)
def actualizar_ingrediente(
    ingrediente_id: int,
    datos_ingrediente: IngredienteActualizar,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    elemento = (
        bd.query(Ingrediente)
        .filter(
            Ingrediente.id == ingrediente_id,
            Ingrediente.usuario_id == usuario_actual.id,
        )
        .first()
    )
    if not elemento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingrediente no encontrado en tu inventario.",
        )

    if datos_ingrediente.nombre is not None:
        elemento.nombre = datos_ingrediente.nombre
    if datos_ingrediente.cantidad is not None:
        elemento.cantidad = datos_ingrediente.cantidad
    if datos_ingrediente.unidad is not None:
        elemento.unidad = datos_ingrediente.unidad

    bd.commit()
    bd.refresh(elemento)
    return elemento


@enrutador.delete(
    "/{ingrediente_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar un ingrediente del inventario",
)
def eliminar_ingrediente(
    ingrediente_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    elemento = (
        bd.query(Ingrediente)
        .filter(
            Ingrediente.id == ingrediente_id,
            Ingrediente.usuario_id == usuario_actual.id,
        )
        .first()
    )
    if not elemento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingrediente no encontrado en tu inventario.",
        )

    bd.delete(elemento)
    bd.commit()
    return {"mensaje": "Ingrediente eliminado correctamente.", "id": ingrediente_id}
