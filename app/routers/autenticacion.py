from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.base_datos import obtener_bd
from app.models import Usuario
from app.schemas import TokenRespuesta, UsuarioCrear, UsuarioLogin, UsuarioRespuesta
from app.seguridad import (
    crear_token_acceso,
    encriptar_contrasena,
    obtener_usuario_actual,
    verificar_contrasena,
)

enrutador = APIRouter(prefix="/api/autenticacion", tags=["Autenticación"])


@enrutador.post(
    "/registro",
    response_model=TokenRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description="Crea una cuenta de usuario en la base de datos y devuelve un token JWT de sesión.",
)
def registrar_usuario(
    datos_usuario: UsuarioCrear,
    bd: Session = Depends(obtener_bd),
):
    existente = (
        bd.query(Usuario)
        .filter(Usuario.email == datos_usuario.email.lower())
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado.",
        )

    nuevo_usuario = Usuario(
        nombre=datos_usuario.nombre,
        email=datos_usuario.email.lower(),
        password_hash=encriptar_contrasena(datos_usuario.password),
    )
    bd.add(nuevo_usuario)
    bd.commit()
    bd.refresh(nuevo_usuario)

    token_acceso = crear_token_acceso(datos={"sub": str(nuevo_usuario.id)})
    return TokenRespuesta(
        access_token=token_acceso,
        token_type="bearer",
        usuario=UsuarioRespuesta.model_validate(nuevo_usuario),
    )


@enrutador.post(
    "/iniciar-sesion",
    response_model=TokenRespuesta,
    summary="Iniciar sesión con correo y contraseña",
    description="Autentica al usuario con sus credenciales y retorna un token JWT.",
)
async def iniciar_sesion_usuario(
    peticion: Request,
    bd: Session = Depends(obtener_bd),
):
    tipo_contenido = peticion.headers.get("content-type", "")
    correo = ""
    contrasena = ""

    if "application/json" in tipo_contenido:
        cuerpo = await peticion.json()
        datos_login = UsuarioLogin(**cuerpo)
        correo = datos_login.email.lower()
        contrasena = datos_login.password
    else:
        formulario = await peticion.form()
        correo = str(formulario.get("username") or formulario.get("email") or "").strip().lower()
        contrasena = str(formulario.get("password") or "")

    if not correo or not contrasena:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe proporcionar correo electrónico y contraseña.",
        )

    usuario = bd.query(Usuario).filter(Usuario.email == correo).first()
    if not usuario or not verificar_contrasena(contrasena, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_acceso = crear_token_acceso(datos={"sub": str(usuario.id)})
    return TokenRespuesta(
        access_token=token_acceso,
        token_type="bearer",
        usuario=UsuarioRespuesta.model_validate(usuario),
    )


@enrutador.get(
    "/perfil",
    response_model=UsuarioRespuesta,
    summary="Obtener perfil del usuario autenticado",
    description="Devuelve la información del usuario propietario del token JWT actual.",
)
def obtener_perfil(usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    return UsuarioRespuesta.model_validate(usuario_actual)
