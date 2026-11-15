from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.configuracion import configuracion

argumentos_conexion = (
    {"check_same_thread": False}
    if configuracion.URL_BASE_DATOS.startswith("sqlite")
    else {}
)

motor = create_engine(
    configuracion.URL_BASE_DATOS,
    connect_args=argumentos_conexion,
    pool_pre_ping=True,
)

SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)

Base = declarative_base()


def obtener_bd():
    bd = SesionLocal()
    try:
        yield bd
    finally:
        bd.close()
