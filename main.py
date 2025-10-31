from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import shutil
import os
import uuid

# --- Importar módulos internos ---
from model.classifier import predict_image
from utils.nutrition_utils import get_nutrition_info
from routers import auth_router, usuario_router, barcode_router  # rutas de /auth/login /auth/register /auth/users ...
from routers import upload_router



# ============================================================
# 🔹 CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================
app = FastAPI(
    title="SaborPeru API 🍲",
    description="API REST para reconocer platos típicos peruanos, obtener su información nutricional y gestionar usuarios.",
    version="1.2.1"
)

# ============================================================
# 🔹 CONFIGURACIÓN DE CARPETAS
# ============================================================
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
# 🔹 REGISTRAR ROUTERS (módulos de rutas)
# ============================================================
app.include_router(auth_router.router)
app.include_router(barcode_router.router)
app.include_router(usuario_router.router)
app.include_router(upload_router.router)

# ============================================================
# 🔹 MODELO DE ENTRADA (para predict_url)
# ============================================================
class ImageURL(BaseModel):
    url: str

# ============================================================
# 🔹 ENDPOINT BASE
# ============================================================
@app.get("/")
def root():
    """Endpoint base de prueba."""
    return {
        "mensaje": "Bienvenido a la API de SaborPeru 🍽️",
        "endpoints": {
            "auth": "/auth/register, /auth/login, /auth/users, /auth/user/{id}",
            "predict_file": "/predict",
            "predict_url": "/predict_url"
        }
    }

# ============================================================
# 🔹 ENDPOINT DE PREDICCIÓN DESDE ARCHIVO
# ============================================================
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Recibe una imagen (archivo), ejecuta el modelo de IA
    y devuelve la información nutricional correspondiente.
    """
    try:
        # Guardar imagen subida
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Predicción del modelo
        result = predict_image(file_path)

        # Obtener información nutricional
        info = get_nutrition_info(result["plato"])
        result["informacion_nutricional"] = info or "No se encontró información nutricional."

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            content={"error": f"Ocurrió un error durante la predicción: {str(e)}"},
            status_code=500
        )

# ============================================================
# 🔹 NUEVO ENDPOINT: PREDICCIÓN DESDE URL
# ============================================================
@app.post("/predict_url")
async def predict_from_url(payload: ImageURL):
    """
    Recibe una URL de imagen, la descarga temporalmente,
    ejecuta la predicción con el modelo y luego elimina la imagen.
    """
    try:
        image_url = payload.url

        # --- Descargar imagen ---
        response = requests.get(image_url, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar la imagen desde la URL proporcionada.")

        # --- Guardar temporalmente ---
        temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, temp_filename)
        with open(file_path, "wb") as f:
            f.write(response.content)

        # --- Ejecutar predicción ---
        result = predict_image(file_path)

        # --- Obtener información nutricional ---
        info = get_nutrition_info(result["plato"])
        result["informacion_nutricional"] = info or "No se encontró información nutricional."

        # --- Eliminar imagen temporal ---
        if os.path.exists(file_path):
            os.remove(file_path)

        return JSONResponse(content=result)

    except HTTPException as e:
        raise e

    except Exception as e:
        return JSONResponse(
            content={"error": f"Ocurrió un error durante la predicción: {str(e)}"},
            status_code=500
        )
