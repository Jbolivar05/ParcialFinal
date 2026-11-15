from unittest.mock import patch
from fastapi.testclient import TestClient

from app.schemas import ItemIngredienteReceta, RecetaEstructuradaLLM


def test_7_endpoint_registro_y_login_jwt(cliente: TestClient):
    respuesta_registro = cliente.post(
        "/api/autenticacion/registro",
        json={
            "nombre": "Carlos Pérez",
            "email": "carlos@unisimon.edu.co",
            "password": "Password123!",
        },
    )
    assert respuesta_registro.status_code == 201
    token = respuesta_registro.json()["access_token"]
    assert token

    respuesta_login = cliente.post(
        "/api/autenticacion/iniciar-sesion",
        json={
            "email": "carlos@unisimon.edu.co",
            "password": "Password123!",
        },
    )
    assert respuesta_login.status_code == 200
    assert "access_token" in respuesta_login.json()

    respuesta_perfil = cliente.get(
        "/api/autenticacion/perfil",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta_perfil.status_code == 200
    assert respuesta_perfil.json()["email"] == "carlos@unisimon.edu.co"


def test_8_endpoint_crud_ingredientes(cliente: TestClient):
    registro = cliente.post(
        "/api/autenticacion/registro",
        json={
            "nombre": "Ana López",
            "email": "ana@unisimon.edu.co",
            "password": "Password123!",
        },
    )
    cabeceras = {"Authorization": f"Bearer {registro.json()['access_token']}"}

    respuesta_crear = cliente.post(
        "/api/ingredientes",
        json={"nombre": "Pasta corta", "cantidad": 250, "unidad": "gramos"},
        headers=cabeceras,
    )
    assert respuesta_crear.status_code == 201
    ingrediente_id = respuesta_crear.json()["id"]

    respuesta_listar = cliente.get("/api/ingredientes", headers=cabeceras)
    assert respuesta_listar.status_code == 200
    assert len(respuesta_listar.json()) == 1

    respuesta_actualizar = cliente.put(
        f"/api/ingredientes/{ingrediente_id}",
        json={"cantidad": 500},
        headers=cabeceras,
    )
    assert respuesta_actualizar.status_code == 200
    assert respuesta_actualizar.json()["cantidad"] == 500.0

    respuesta_eliminar = cliente.delete(
        f"/api/ingredientes/{ingrediente_id}",
        headers=cabeceras,
    )
    assert respuesta_eliminar.status_code == 200


def test_9_endpoint_generar_calificar_y_eliminar_receta(cliente: TestClient):
    registro = cliente.post(
        "/api/autenticacion/registro",
        json={
            "nombre": "Laura Gómez",
            "email": "laura@unisimon.edu.co",
            "password": "Password123!",
        },
    )
    cabeceras = {"Authorization": f"Bearer {registro.json()['access_token']}"}

    cliente.post(
        "/api/ingredientes",
        json={"nombre": "Pechuga de pollo", "cantidad": 400, "unidad": "gramos"},
        headers=cabeceras,
    )

    salida_simulada_llm = RecetaEstructuradaLLM(
        nombre_del_plato="Pollo a la Plancha con Finas Hierbas",
        ingredientes=[
            ItemIngredienteReceta(nombre="Pechuga de pollo", cantidad="400 gramos")
        ],
        pasos_de_preparacion=[
            "Filetear la pechuga de pollo y sazonar con sal y pimienta.",
            "Dorar en sartén caliente durante 6 minutos por cada lado.",
        ],
        tiempo_estimado="15 minutos",
        nivel_de_dificultad="Fácil",
    )

    with patch(
        "app.routers.recetas.generar_receta_desde_inventario",
        return_value=salida_simulada_llm,
    ):
        respuesta_generar = cliente.post(
            "/api/recetas/generar",
            json={"tipo_comida": "Cena saludable"},
            headers=cabeceras,
        )
        assert respuesta_generar.status_code == 201
        datos_receta = respuesta_generar.json()
        receta_id = datos_receta["id"]
        assert datos_receta["nombre_del_plato"] == "Pollo a la Plancha con Finas Hierbas"

    respuesta_calificar = cliente.post(
        f"/api/recetas/{receta_id}/calificar",
        json={"puntuacion": 5, "comentario": "Deliciosa y muy rápida."},
        headers=cabeceras,
    )
    assert respuesta_calificar.status_code == 201
    assert respuesta_calificar.json()["puntuacion"] == 5

    respuesta_historial = cliente.get("/api/recetas", headers=cabeceras)
    assert respuesta_historial.status_code == 200
    assert respuesta_historial.json()[0]["promedio_calificacion"] == 5.0

    respuesta_eliminar = cliente.delete(
        f"/api/recetas/{receta_id}",
        headers=cabeceras,
    )
    assert respuesta_eliminar.status_code == 200


def test_10_endpoint_salud_favicon_y_cloudflare_https(cliente: TestClient):
    respuesta_salud = cliente.get(
        "/api/salud",
        headers={"X-Forwarded-Proto": "https"},
    )
    assert respuesta_salud.status_code == 200
    assert respuesta_salud.json()["estado"] == "ok"
    assert respuesta_salud.json()["protocolo"] == "https"

    respuesta_favicon = cliente.get("/favicon.ico")
    assert respuesta_favicon.status_code == 200
