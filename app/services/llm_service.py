import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.configuracion import configuracion
from app.schemas import ItemIngredienteReceta, RecetaEstructuradaLLM

registro = logging.getLogger(__name__)


def validar_ingredientes_inventario(ingredientes: List[Any]) -> List[Dict[str, Any]]:
    if not ingredientes:
        raise ValueError(
            "El inventario está vacío. Agrega al menos un ingrediente antes de generar una receta."
        )

    normalizados: List[Dict[str, Any]] = []
    for elemento in ingredientes:
        if isinstance(elemento, dict):
            nombre = str(elemento.get("nombre", "")).strip()
            cantidad = elemento.get("cantidad", 0)
            unidad = str(elemento.get("unidad", "unidades")).strip()
        else:
            nombre = str(getattr(elemento, "nombre", "")).strip()
            cantidad = getattr(elemento, "cantidad", 0)
            unidad = str(getattr(elemento, "unidad", "unidades")).strip()

        if len(nombre) < 2 or nombre.isdigit():
            raise ValueError(f"Ingrediente inválido en el inventario: '{nombre}'.")
        try:
            cantidad_numerica = float(cantidad)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Cantidad inválida para el ingrediente '{nombre}'.") from exc

        if cantidad_numerica <= 0:
            raise ValueError(
                f"La cantidad del ingrediente '{nombre}' debe ser mayor que cero."
            )
        if not unidad:
            unidad = "unidades"

        normalizados.append(
            {
                "nombre": nombre,
                "cantidad": cantidad_numerica,
                "unidad": unidad,
            }
        )

    return normalizados


def construir_prompt_receta(
    ingredientes: List[Any],
    tipo_comida: Optional[str] = None,
) -> str:
    validados = validar_ingredientes_inventario(ingredientes)
    lineas_inventario = [
        f"- {item['nombre']}: {item['cantidad']:g} {item['unidad']}"
        for item in validados
    ]
    texto_inventario = "\n".join(lineas_inventario)
    linea_preferencia = (
        f"\nPreferencia o categoría solicitada: {tipo_comida.strip()}."
        if tipo_comida and tipo_comida.strip()
        else ""
    )

    prompt = (
        "Eres un chef profesional experto en cocina casera y aprovechamiento de inventario.\n"
        "Genera UNA receta deliciosa y realista utilizando principalmente los siguientes "
        "ingredientes disponibles en casa (puedes asumir condimentos básicos como sal, "
        "pimienta, agua o aceite):\n\n"
        f"INVENTARIO DISPONIBLE:\n{texto_inventario}{linea_preferencia}\n\n"
        "DEBES responder ÚNICAMENTE con un objeto JSON válido, sin texto adicional ni explicaciones, "
        "siguiendo exactamente esta estructura:\n"
        "{\n"
        '  "nombre_del_plato": "Nombre atractivo de la receta",\n'
        '  "ingredientes": [\n'
        '    {"nombre": "Nombre del ingrediente", "cantidad": "Cantidad y unidad exacta"}\n'
        "  ],\n"
        '  "pasos_de_preparacion": [\n'
        '    "Paso 1 detallado...",\n'
        '    "Paso 2 detallado..."\n'
        "  ],\n"
        '  "tiempo_estimado": "Ej: 25 minutos",\n'
        '  "nivel_de_dificultad": "Fácil | Media | Alta"\n'
        "}"
    )
    return prompt


def parsear_respuesta_receta_llm(respuesta_cruda: str) -> RecetaEstructuradaLLM:
    if not respuesta_cruda or not respuesta_cruda.strip():
        raise ValueError("La respuesta del modelo de lenguaje está vacía.")

    limpio = respuesta_cruda.strip()

    coincidencia_bloque = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", limpio, re.DOTALL)
    if coincidencia_bloque:
        limpio = coincidencia_bloque.group(1)
    else:
        inicio = limpio.find("{")
        fin = limpio.rfind("}")
        if inicio != -1 and fin != -1 and fin > inicio:
            limpio = limpio[inicio : fin + 1]

    try:
        datos = json.loads(limpio)
    except json.JSONDecodeError as exc:
        raise ValueError(f"La respuesta del LLM no es un JSON válido: {exc}") from exc

    if not isinstance(datos, dict):
        raise ValueError("El JSON devuelto por el LLM debe ser un objeto.")

    nombre_del_plato = (
        datos.get("nombre_del_plato")
        or datos.get("nombre_plato")
        or datos.get("nombre")
    )
    ingredientes_crudos = (
        datos.get("ingredientes")
        or datos.get("lista_de_ingredientes")
        or datos.get("lista_ingredientes")
    )
    pasos_crudos = (
        datos.get("pasos_de_preparacion")
        or datos.get("pasos_preparacion")
        or datos.get("pasos")
    )
    tiempo_estimado = datos.get("tiempo_estimado") or datos.get("tiempo")
    nivel_de_dificultad = (
        datos.get("nivel_de_dificultad")
        or datos.get("nivel_dificultad")
        or datos.get("dificultad")
    )

    if not nombre_del_plato or not ingredientes_crudos or not pasos_crudos or not tiempo_estimado or not nivel_de_dificultad:
        raise ValueError(
            "El JSON del LLM no contiene todos los campos obligatorios "
            "(nombre_del_plato, ingredientes, pasos_de_preparacion, tiempo_estimado, nivel_de_dificultad)."
        )

    ingredientes_normalizados: List[ItemIngredienteReceta] = []
    if isinstance(ingredientes_crudos, list):
        for ing in ingredientes_crudos:
            if isinstance(ing, dict):
                nombre_ing = str(ing.get("nombre") or ing.get("ingrediente") or "").strip()
                cantidad_ing = str(ing.get("cantidad") or "Al gusto").strip()
                if nombre_ing:
                    ingredientes_normalizados.append(
                        ItemIngredienteReceta(nombre=nombre_ing, cantidad=cantidad_ing)
                    )
            elif isinstance(ing, str) and ing.strip():
                partes = ing.split(":", 1)
                if len(partes) == 2:
                    ingredientes_normalizados.append(
                        ItemIngredienteReceta(nombre=partes[0].strip(), cantidad=partes[1].strip())
                    )
                else:
                    ingredientes_normalizados.append(
                        ItemIngredienteReceta(nombre=ing.strip(), cantidad="Cantidad necesaria")
                    )

    pasos_normalizados: List[str] = []
    if isinstance(pasos_crudos, list):
        pasos_normalizados = [str(paso).strip() for paso in pasos_crudos if str(paso).strip()]
    elif isinstance(pasos_crudos, str) and pasos_crudos.strip():
        pasos_normalizados = [
            linea.strip() for linea in pasos_crudos.splitlines() if linea.strip()
        ]

    return RecetaEstructuradaLLM(
        nombre_del_plato=str(nombre_del_plato).strip(),
        ingredientes=ingredientes_normalizados,
        pasos_de_preparacion=pasos_normalizados,
        tiempo_estimado=str(tiempo_estimado).strip(),
        nivel_de_dificultad=str(nivel_de_dificultad).strip(),
    )


def _construir_receta_respaldo(
    ingredientes_validados: List[Dict[str, Any]],
    tipo_comida: Optional[str] = None,
) -> RecetaEstructuradaLLM:
    nombres_principales = [item["nombre"] for item in ingredientes_validados[:3]]
    sufijo_plato = f" ({tipo_comida.strip()})" if tipo_comida and tipo_comida.strip() else ""
    nombre_plato = f"Salteado Casero de {', '.join(nombres_principales)}{sufijo_plato}"

    ingredientes_receta = [
        ItemIngredienteReceta(
            nombre=item["nombre"],
            cantidad=f"{item['cantidad']:g} {item['unidad']}",
        )
        for item in ingredientes_validados
    ]
    ingredientes_receta.append(
        ItemIngredienteReceta(nombre="Sal, pimienta y aceite", cantidad="Al gusto")
    )

    pasos = [
        f"Lava, desinfecta y corta en porciones uniformes los ingredientes principales: {', '.join(nombres_principales)}.",
        "Calienta una sartén amplia a fuego medio con una cucharada de aceite durante 2 minutos.",
        "Incorpora primero los ingredientes de cocción más firme y sofríe durante 8 a 10 minutos removiendo constantemente.",
        "Añade el resto de los ingredientes del inventario, condimenta con sal y pimienta al gusto y cocina por 7 minutos adicionales.",
        "Verifica la cocción, rectifica el sazón y sirve caliente.",
    ]

    return RecetaEstructuradaLLM(
        nombre_del_plato=nombre_plato,
        ingredientes=ingredientes_receta,
        pasos_de_preparacion=pasos,
        tiempo_estimado="25 minutos",
        nivel_de_dificultad="Fácil",
    )


def generar_receta_desde_inventario(
    ingredientes: List[Any],
    tipo_comida: Optional[str] = None,
) -> RecetaEstructuradaLLM:
    validados = validar_ingredientes_inventario(ingredientes)
    prompt = construir_prompt_receta(validados, tipo_comida=tipo_comida)

    clave_api = (configuracion.CLAVE_API_LLM or "").strip()
    es_marcador = (
        not clave_api
        or clave_api == "tu_api_key_de_openrouter_aqui"
        or clave_api.startswith("tu_api_key")
    )

    if es_marcador:
        registro.warning(
            "LLM_API_KEY no configurada en .env; usando generador estructurado de respaldo."
        )
        return _construir_receta_respaldo(validados, tipo_comida=tipo_comida)

    cabeceras = {
        "Authorization": f"Bearer {clave_api}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://unisimon-recetas.app",
        "X-Title": "Proyecto Final Generador de Recetas IA",
    }

    carga_util = {
        "model": configuracion.MODELO_LLM,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un servicio interno generador de recetas culinarias que responde "
                    "exclusivamente en formato JSON válido."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    try:
        with httpx.Client(timeout=35.0) as cliente_http:
            respuesta = cliente_http.post(
                configuracion.URL_API_LLM,
                headers=cabeceras,
                json=carga_util,
            )
            respuesta.raise_for_status()
            cuerpo = respuesta.json()
            contenido_crudo = cuerpo["choices"][0]["message"]["content"]
            return parsear_respuesta_receta_llm(contenido_crudo)
    except Exception as exc:
        registro.error("Error al consultar proveedor LLM (%s): %s", configuracion.MODELO_LLM, exc)
        return _construir_receta_respaldo(validados, tipo_comida=tipo_comida)
