import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.base_datos import Base, obtener_bd
from app.main import app

URL_BD_PRUEBAS = "sqlite://"

motor_pruebas = create_engine(
    URL_BD_PRUEBAS,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SesionPruebasLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=motor_pruebas,
)


def sobreescribir_obtener_bd():
    bd = SesionPruebasLocal()
    try:
        yield bd
    finally:
        bd.close()


app.dependency_overrides[obtener_bd] = sobreescribir_obtener_bd


@pytest.fixture(autouse=True)
def configurar_base_datos():
    Base.metadata.create_all(bind=motor_pruebas)
    yield
    Base.metadata.drop_all(bind=motor_pruebas)


@pytest.fixture
def cliente():
    return TestClient(app)
