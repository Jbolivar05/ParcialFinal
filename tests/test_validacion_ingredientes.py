import pytest

from app.schemas import IngredienteCrear
from app.services.llm_service import validar_ingredientes_inventario


def test_1_validacion_esquema_ingrediente_correcto():
    ingrediente = IngredienteCrear(
        nombre="  Tomate Chonto  ",
        cantidad=4.5,
        unidad="unidades",
    )
    assert ingrediente.nombre == "Tomate Chonto"
    assert ingrediente.cantidad == 4.5
    assert ingrediente.unidad == "unidades"


def test_2_validacion_esquema_ingrediente_invalido():
    with pytest.raises(ValueError):
        IngredienteCrear(nombre="Arroz", cantidad=0, unidad="gramos")

    with pytest.raises(ValueError):
        IngredienteCrear(nombre="123456", cantidad=250, unidad="gramos")


def test_3_validacion_inventario_servicio_llm():
    with pytest.raises(ValueError, match="inventario está vacío"):
        validar_ingredientes_inventario([])

    with pytest.raises(ValueError, match="mayor que cero"):
        validar_ingredientes_inventario(
            [{"nombre": "Cebolla cabezona", "cantidad": -1, "unidad": "unidades"}]
        )
