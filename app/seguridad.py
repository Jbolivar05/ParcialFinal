from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.base_datos import obtener_bd
from app.configuracion import configuracion
from app.models import Usuario

esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/autenticacion/iniciar-sesion")


def encriptar_contrasena(contrasena: str) -> str:
    sal = secrets.token_hex(16)
    clave_derivada = hashlib.pbkdf2_hmac(
        "sha256",
        contrasena.encode("utf-8"),
        sal.encode("utf-8"),
        260000,
    )
    return f"pbkdf2_sha256$260000${sal}${clave_derivada.hex()}"


def verificar_contrasena(contrasena_plana: str, contrasena_encriptada: str) -> bool:
    try:
        algoritmo, iteraciones, sal, hash_guardado = contrasena_encriptada.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        clave_derivada = hashlib.pbkdf2_hmac(
            "sha256",
            contrasena_plana.encode("utf-8"),
            sal.encode("utf-8"),
            int(iteraciones),
        )
        return hmac.compare_digest(clave_derivada.hex(), hash_guardado)
    except Exception:
        return False


def crear_token_acceso(
    datos: dict,
    tiempo_expiracion: Optional[timedelta] = None,
) -> str:
    datos_codificar = datos.copy()
    expiracion = datetime.now(timezone.utc) + (
        tiempo_expiracion
        if tiempo_expiracion
        else timedelta(minutes=configuracion.MINUTOS_EXPIRACION_TOKEN)
    )
    datos_codificar.update({"exp": expiracion})
    return jwt.encode(
        datos_codificar,
        configuracion.CLAVE_SECRETA_JWT,
        algorithm=configuracion.ALGORITMO_JWT,
    )


def decodificar_token_acceso(token: str) -> dict:
    try:
        carga_util = jwt.decode(
            token,
            configuracion.CLAVE_SECRETA_JWT,
            algorithms=[configuracion.ALGORITMO_JWT],
        )
        return carga_util
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de sesión ha expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def obtener_usuario_actual(
    token: str = Depends(esquema_oauth2),
    bd: Session = Depends(obtener_bd),
) -> Usuario:
    carga_util = decodificar_token_acceso(token)
    usuario_id = carga_util.get("sub")
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    usuario = bd.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario
