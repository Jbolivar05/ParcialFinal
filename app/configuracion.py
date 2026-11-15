import os
from dotenv import load_dotenv

load_dotenv()


class Configuracion:
    NOMBRE_PROYECTO: str = "Generador de Recetas con Inventario e IA"
    VERSION: str = "1.0.0"
    ENTORNO_APP: str = os.getenv("APP_ENV", "desarrollo")
    URL_BASE_DATOS: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./.venv/recetas_local.db",
    )
    CLAVE_SECRETA_JWT: str = os.getenv(
        "JWT_SECRET_KEY",
        "clave_secreta_desarrollo_cambiar_en_produccion_1234567890",
    )
    ALGORITMO_JWT: str = os.getenv("JWT_ALGORITHM", "HS256")
    MINUTOS_EXPIRACION_TOKEN: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    CLAVE_API_LLM: str = os.getenv("LLM_API_KEY", "")
    URL_API_LLM: str = os.getenv(
        "LLM_API_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    )
    MODELO_LLM: str = os.getenv(
        "LLM_MODEL",
        "meta-llama/llama-3.1-8b-instruct:free",
    )


configuracion = Configuracion()
