from fastapi import APIRouter, UploadFile, File, HTTPException
import boto3, uuid, os
from dotenv import load_dotenv

# Cargar credenciales del archivo .env
load_dotenv()

router = APIRouter(prefix="/upload", tags=["Upload"])

# Variables desde .env
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key")
AWS_SESSION_TOKEN = os.getenv("aws_session_token")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
S3_FOLDER = os.getenv("AWS_S3_FOLDER")

# Crear cliente autenticado de S3
s3 = boto3.client(
    "s3",
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

import mimetypes

@router.post("/profile-image")
async def upload_profile_image(file: UploadFile = File(...)):
    try:
        # Generar nombre único
        file_extension = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        s3_key = f"{S3_FOLDER}{unique_name}"

        # Deducir Content-Type correcto
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "image/jpeg"
        if mime_type == "image/*":  # <- corrige casos ambiguos
            mime_type = "image/jpeg"

        # Subir a S3 con tipo MIME forzado
        s3.upload_fileobj(
            file.file,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": mime_type
            }
        )

        # Construir URL pública
        public_url = f"https://{BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{s3_key}"

        return {
            "status": "success",
            "file_name": unique_name,
            "content_type": mime_type,
            "url": public_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir: {str(e)}")

# ===========================================================
# 🍽️ Subida de imagen de comida (historial)
# ===========================================================
@router.post("/meal-image")
async def upload_meal_image(file: UploadFile = File(...)):
    """
    🍲 Sube la imagen de una comida (escaneada o reconocida) al bucket S3.
    Solo devuelve la URL pública — no guarda en base de datos.
    """
    try:
        ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{ext}"
        s3_key = f"{S3_FOLDER}history/{unique_name}"

        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "image/jpeg"
        if mime_type == "image/*":
            mime_type = "image/jpeg"

        s3.upload_fileobj(
            file.file,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={"ACL": "public-read", "ContentType": mime_type}
        )

        public_url = f"https://{BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{s3_key}"
        return {"status": "success", "type": "meal", "url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen de comida: {str(e)}")
