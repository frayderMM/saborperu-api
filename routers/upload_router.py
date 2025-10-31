from fastapi import APIRouter, UploadFile, File, HTTPException
import boto3, uuid, os
from dotenv import load_dotenv

# Cargar credenciales del archivo .env
load_dotenv()

router = APIRouter(prefix="/upload", tags=["Upload"])

# Variables desde .env
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
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

@router.post("/profile-image")
async def upload_profile_image(file: UploadFile = File(...)):
    """
    Sube una imagen al bucket S3 y devuelve la URL pública.
    """
    try:
        # Generar nombre único
        file_extension = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        s3_key = f"{S3_FOLDER}{unique_name}"

        # Subir el archivo a S3
        s3.upload_fileobj(
            file.file,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={
                "ContentType": file.content_type,
                "ACL": "public-read"
            }
        )

        # Construir URL pública
        public_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        return {
            "status": "success",
            "file_name": unique_name,
            "url": public_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir: {str(e)}")
