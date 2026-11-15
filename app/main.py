from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.base_datos import Base, motor
from app.configuracion import configuracion
from app.routers import autenticacion, ingredientes, recetas

DIRECTORIO_BASE = Path(__file__).resolve().parent.parent
DIRECTORIO_ESTATICOS = DIRECTORIO_BASE / "static"
DIRECTORIO_PLANTILLAS = Path(__file__).resolve().parent / "templates"


@asynccontextmanager
async def ciclo_vida(aplicacion: FastAPI):
    Base.metadata.create_all(bind=motor)
    yield


app = FastAPI(
    title=configuracion.NOMBRE_PROYECTO,
    version=configuracion.VERSION,
    description=(
        "API RESTful desarrollada con Python y FastAPI para gestionar el inventario "
        "personal de ingredientes en casa y generar recetas estructuradas mediante "
        "Inteligencia Artificial (OpenRouter LLM), con autenticación JWT y persistencia en MySQL."
    ),
    lifespan=ciclo_vida,
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(DIRECTORIO_ESTATICOS)), name="static")
plantillas = Jinja2Templates(directory=str(DIRECTORIO_PLANTILLAS))

app.include_router(autenticacion.enrutador)
app.include_router(ingredientes.enrutador)
app.include_router(recetas.enrutador)


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def servir_inicio(peticion: Request):
    return plantillas.TemplateResponse(request=peticion, name="index.html")


@app.get(
    "/favicon.ico",
    include_in_schema=False,
)
def servir_favicon():
    return FileResponse(DIRECTORIO_ESTATICOS / "favicon.ico", media_type="image/x-icon")


@app.get(
    "/api/salud",
    tags=["Sistema"],
    summary="Verificar estado del servidor",
)
def verificar_salud(peticion: Request):
    esquema = peticion.headers.get("x-forwarded-proto", peticion.url.scheme)
    return {
        "estado": "ok",
        "proyecto": configuracion.NOMBRE_PROYECTO,
        "version": configuracion.VERSION,
        "protocolo": esquema,
    }
