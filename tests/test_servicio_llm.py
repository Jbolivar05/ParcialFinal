import json
import pytest

from app.schemas import RecetaEstructuradaLLM
from app.services.llm_service import (
    construir_prompt_receta,
    parsear_respuesta_receta_llm,
)


def test_4_generacion_prompt_estructurado():
    inventario = [
        {"nombre": "Arroz blanco", "cantidad": 300, "unidad": "gramos"},
        {"nombre": "Huevos", "cantidad": 3, "unidad": "unidades"},
    ]
    prompt = construir_prompt_receta(inventario, tipo_comida="Almuerzo rápido")

    assert "Arroz blanco: 300 gramos" in prompt
    assert "Huevos: 3 unidades" in prompt
    assert "Almuerzo rápido" in prompt
    assert "nombre_del_plato" in prompt
    assert "ingredientes" in prompt
    assert "pasos_de_preparacion" in prompt
    assert "tiempo_estimado" in prompt
    assert "nivel_de_dificultad" in prompt


def test_5_parseo_respuesta_llm_json_valido_y_markdown():
    respuesta_simulada = """```json
    {
      "nombre_del_plato": "Arroz salteado con huevo",
      "ingredientes": [
        {"nombre": "Arroz blanco", "cantidad": "300 gramos"},
        {"nombre": "Huevos", "cantidad": "3 unidades"}
      ],
      "pasos_de_preparacion": [
        "Cocinar el arroz blanco con una pizca de sal.",
        "Batir los huevos y saltearlos junto con el arroz caliente."
      ],
      "tiempo_estimado": "20 minutos",
      "nivel_de_dificultad": "Fácil"
    }
    ```"""

    receta = parsear_respuesta_receta_llm(respuesta_simulada)
    assert isinstance(receta, RecetaEstructuradaLLM)
    assert receta.nombre_del_plato == "Arroz salteado con huevo"
    assert len(receta.ingredientes) == 2
    assert len(receta.pasos_de_preparacion) == 2
    assert receta.tiempo_estimado == "20 minutos"
    assert receta.nivel_de_dificultad == "Fácil"


def test_6_parseo_respuesta_llm_incompleta_lanza_error():
    json_incompleto = json.dumps({"nombre_del_plato": "Plato incompleto"})
    with pytest.raises(ValueError, match="campos obligatorios"):
        parsear_respuesta_receta_llm(json_incompleto)
