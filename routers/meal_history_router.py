from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from model.database import SessionLocal, MealHistory
from model.schemas_meal import MealHistoryCreate, MealHistoryResponse
from datetime import datetime
import boto3, os, uuid, mimetypes
from dotenv import load_dotenv
from model.database import SessionLocal, MealHistory, Usuario

# ===========================================================
# 🔹 Configuración inicial
# ===========================================================
router = APIRouter(prefix="/meal-history", tags=["Meal History"])
load_dotenv()

# Variables de entorno AWS
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key")
AWS_SESSION_TOKEN = os.getenv("aws_session_token")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
S3_FOLDER = os.getenv("AWS_S3_FOLDER")

# Cliente S3 autenticado
s3 = boto3.client(
    "s3",
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

# ===========================================================
# 🔹 Dependencia DB
# ===========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===========================================================
# 🔹 Crear registro de comida
# ===========================================================
@router.post("/", response_model=MealHistoryResponse)
def create_meal(record: MealHistoryCreate, db: Session = Depends(get_db)):
    db_record = MealHistory(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

# ===========================================================
# 🔹 Obtener historial de un usuario
# ===========================================================
@router.get("/{usuario_id}", response_model=list[MealHistoryResponse])
def get_user_history(usuario_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(MealHistory)
        .filter(MealHistory.usuario_id == usuario_id)
        .order_by(MealHistory.created_at.desc())
        .all()
    )
    if not records:
        raise HTTPException(status_code=404, detail="No se encontró historial para este usuario.")
    return records
# ===========================================================
# 📤 Subir imagen de comida y guardar registro en BD
# ===========================================================
@router.post("/upload")
async def upload_meal_image(
    usuario_id: int = Form(...),
    meal_name: str = Form(...),
    method: str = Form(...),
    confidence: float = Form(0.0),
    calories: float = Form(0.0),
    proteins: float = Form(0.0),
    fats: float = Form(0.0),
    carbs: float = Form(0.0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 1️⃣ Subir imagen a AWS S3
        file_extension = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4()}.{file_extension}"
        s3_key = f"{S3_FOLDER}meal_history/{unique_name}"

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

        # 2️⃣ Guardar registro en MySQL
        new_record = MealHistory(
            usuario_id=usuario_id,
            meal_name=meal_name,
            method=method,
            confidence=confidence,
            calories=calories,
            proteins=proteins,
            fats=fats,
            carbs=carbs,
            image_url=public_url,
            created_at=datetime.utcnow()
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return {
            "status": "success",
            "message": "Comida registrada exitosamente 🍽️",
            "meal_id": new_record.id,
            "image_url": public_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir o guardar: {str(e)}")

@router.get("/latest-by-user/{user_id}", response_model=MealHistoryResponse)
def get_latest_by_user(user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.user_id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    latest_meal = (
        db.query(MealHistory)
        .filter(MealHistory.usuario_id == usuario.id)
        .order_by(MealHistory.created_at.desc())
        .first()
    )
    if not latest_meal:
        raise HTTPException(status_code=404, detail="No hay comidas registradas aún.")
    
    return latest_meal
