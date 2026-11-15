import json
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.base_datos import obtener_bd
from app.models import Calificacion, Ingrediente, Receta, Usuario
from app.schemas import (
    CalificacionCrear,
    CalificacionRespuesta,
    ItemIngredienteReceta,
    RecetaRespuesta,
    SolicitudGenerarReceta,
)
from app.seguridad import obtener_usuario_actual
from app.services.llm_service import generar_receta_desde_inventario

enrutador = APIRouter(prefix="/api/recetas", tags=["Recetas e Inteligencia Artificial"])


def _serializar_receta(receta: Receta, usuario_actual_id: int) -> RecetaRespuesta:
    try:
        ingredientes_crudos = json.loads(receta.ingredientes_json)
    except Exception:
        ingredientes_crudos = []

    try:
        pasos_crudos = json.loads(receta.pasos_preparacion)
    except Exception:
        pasos_crudos = []

    lista_ingredientes = [
        ItemIngredienteReceta(
            nombre=str(i.get("nombre", "")),
            cantidad=str(i.get("cantidad", "")),
        )
        for i in ingredientes_crudos
        if isinstance(i, dict)
    ]

    calificaciones = receta.calificaciones or []
    promedio_calificacion = (
        round(sum(c.puntuacion for c in calificaciones) / len(calificaciones), 2)
        if calificaciones
        else None
    )
    mi_calificacion = next(
        (c.puntuacion for c in calificaciones if c.usuario_id == usuario_actual_id),
        None,
    )

    return RecetaRespuesta(
        id=receta.id,
        usuario_id=receta.usuario_id,
        nombre_del_plato=receta.nombre_plato,
        ingredientes=lista_ingredientes,
        pasos_de_preparacion=[str(p) for p in pasos_crudos],
        tiempo_estimado=receta.tiempo_estimado,
        nivel_de_dificultad=receta.nivel_dificultad,
        guardada=receta.guardada,
        promedio_calificacion=promedio_calificacion,
        mi_calificacion=mi_calificacion,
        calificaciones=[
            CalificacionRespuesta.model_validate(c) for c in calificaciones
        ],
        fecha_creacion=receta.fecha_creacion,
    )


@enrutador.post(
    "/generar",
    response_model=RecetaRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Generar receta con IA a partir del inventario actual",
    description=(
        "Toma los ingredientes registrados en el inventario del usuario, invoca el servicio "
        "interno de LLM (OpenRouter), valida la estructura JSON devuelta y almacena la receta en la base de datos."
    ),
)
def generar_receta(
    datos_solicitud: Optional[SolicitudGenerarReceta] = Body(default=None),
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    elementos_inventario = (
        bd.query(Ingrediente)
        .filter(Ingrediente.usuario_id == usuario_actual.id)
        .all()
    )
    if not elementos_inventario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tienes ingredientes en tu inventario. Agrega ingredientes antes de generar una receta.",
        )

    tipo_comida = datos_solicitud.tipo_comida if datos_solicitud else None
    try:
        receta_llm = generar_receta_desde_inventario(
            elementos_inventario,
            tipo_comida=tipo_comida,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    nueva_receta = Receta(
        usuario_id=usuario_actual.id,
        nombre_plato=receta_llm.nombre_del_plato,
        ingredientes_json=json.dumps(
            [item.model_dump() for item in receta_llm.ingredientes],
            ensure_ascii=False,
        ),
        pasos_preparacion=json.dumps(
            receta_llm.pasos_de_preparacion,
            ensure_ascii=False,
        ),
        tiempo_estimado=receta_llm.tiempo_estimado,
        nivel_dificultad=receta_llm.nivel_de_dificultad,
        guardada=True,
    )
    bd.add(nueva_receta)
    bd.commit()
    bd.refresh(nueva_receta)

    return _serializar_receta(nueva_receta, usuario_actual.id)


@enrutador.get(
    "",
    response_model=List[RecetaRespuesta],
    summary="Listar historial de recetas generadas",
    description="Devuelve todas las recetas generadas previamente por el usuario autenticado.",
)
def listar_recetas(
    solo_guardadas: bool = False,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    consulta = bd.query(Receta).filter(Receta.usuario_id == usuario_actual.id)
    if solo_guardadas:
        consulta = consulta.filter(Receta.guardada.is_(True))
    recetas = consulta.order_by(Receta.fecha_creacion.desc()).all()
    return [_serializar_receta(r, usuario_actual.id) for r in recetas]


@enrutador.get(
    "/{receta_id}",
    response_model=RecetaRespuesta,
    summary="Obtener detalle de una receta",
)
def obtener_receta(
    receta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    receta = (
        bd.query(Receta)
        .filter(Receta.id == receta_id, Receta.usuario_id == usuario_actual.id)
        .first()
    )
    if not receta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receta no encontrada.",
        )
    return _serializar_receta(receta, usuario_actual.id)


@enrutador.patch(
    "/{receta_id}/guardar",
    response_model=RecetaRespuesta,
    summary="Guardar o desmarcar una receta como favorita",
)
def alternar_guardar_receta(
    receta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    receta = (
        bd.query(Receta)
        .filter(Receta.id == receta_id, Receta.usuario_id == usuario_actual.id)
        .first()
    )
    if not receta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receta no encontrada.",
        )

    receta.guardada = not receta.guardada
    bd.commit()
    bd.refresh(receta)
    return _serializar_receta(receta, usuario_actual.id)


@enrutador.post(
    "/{receta_id}/calificar",
    response_model=CalificacionRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Calificar una receta (1 a 5 estrellas)",
    description="Permite al usuario calificar una receta generada con una puntuación de 1 a 5 estrellas y comentario opcional.",
)
def calificar_receta(
    receta_id: int,
    datos_calificacion: CalificacionCrear,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    receta = (
        bd.query(Receta)
        .filter(Receta.id == receta_id, Receta.usuario_id == usuario_actual.id)
        .first()
    )
    if not receta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receta no encontrada.",
        )

    calificacion_existente = (
        bd.query(Calificacion)
        .filter(
            Calificacion.receta_id == receta_id,
            Calificacion.usuario_id == usuario_actual.id,
        )
        .first()
    )

    if calificacion_existente:
        calificacion_existente.puntuacion = datos_calificacion.puntuacion
        calificacion_existente.comentario = datos_calificacion.comentario
        bd.commit()
        bd.refresh(calificacion_existente)
        return calificacion_existente

    nueva_calificacion = Calificacion(
        receta_id=receta_id,
        usuario_id=usuario_actual.id,
        puntuacion=datos_calificacion.puntuacion,
        comentario=datos_calificacion.comentario,
    )
    bd.add(nueva_calificacion)
    bd.commit()
    bd.refresh(nueva_calificacion)
    return nueva_calificacion


@enrutador.delete(
    "/{receta_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar una receta del historial",
)
def eliminar_receta(
    receta_id: int,
    bd: Session = Depends(obtener_bd),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    receta = (
        bd.query(Receta)
        .filter(Receta.id == receta_id, Receta.usuario_id == usuario_actual.id)
        .first()
    )
    if not receta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receta no encontrada.",
        )

    bd.delete(receta)
    bd.commit()
    return {"mensaje": "Receta eliminada del historial correctamente.", "id": receta_id}
