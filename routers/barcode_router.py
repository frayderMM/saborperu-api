from fastapi import APIRouter, UploadFile, File, HTTPException
from pyzbar.pyzbar import decode
import numpy as np
import cv2
import requests

router = APIRouter(prefix="/barcode", tags=["Barcode"])

# ==========================================================
# 📸 1️⃣ Endpoint: Leer código de barras desde imagen
# ==========================================================
@router.post("/read")
async def read_barcode(file: UploadFile = File(...)):
    """
    Recibe una imagen (foto) y devuelve el código de barras detectado.
    Tolerante a ruido, desenfoque, rotaciones y códigos pequeños en productos.
    """
    try:
        # Leer bytes e imagen
        image_bytes = await file.read()
        npimg = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Imagen inválida o no soportada")

        # ==========================================================
        # 🧩 1. Preprocesamiento adaptativo
        # ==========================================================
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        gray = cv2.equalizeHist(gray)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)

        # ==========================================================
        # 🧩 2. Intento de decodificación directa
        # ==========================================================
        decoded = decode(blur)
        results = []

        # ==========================================================
        # 🧩 3. Si no hay resultados, buscar regiones tipo código
        # ==========================================================
        if not decoded:
            gradX = cv2.Sobel(blur, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
            gradY = cv2.Sobel(blur, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
            gradient = cv2.subtract(gradX, gradY)
            gradient = cv2.convertScaleAbs(gradient)
            gradient = cv2.morphologyEx(gradient, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
            thresh = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect = w / float(h)
                if 2.0 < aspect < 8.0 and w > 60 and h > 20:
                    roi = gray[y:y+h, x:x+w]
                    roi = cv2.resize(roi, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                    roi = cv2.GaussianBlur(roi, (3, 3), 0)
                    roi_decoded = decode(roi)
                    if roi_decoded:
                        decoded.extend(roi_decoded)

        # ==========================================================
        # 🧩 4. Rotaciones y reescalados (para ángulos o códigos pequeños)
        # ==========================================================
        if not decoded:
            for angle in [90, 180, 270]:
                rot = cv2.rotate(gray, getattr(cv2, f"ROTATE_{angle}_CLOCKWISE"))
                scaled = cv2.resize(rot, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
                decoded_rot = decode(scaled)
                if decoded_rot:
                    decoded.extend(decoded_rot)
                    break

        # ==========================================================
        # 🧩 5. Si no se detecta, aplicar detección basada en contraste local
        # ==========================================================
        if not decoded:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
            decoded_clahe = decode(enhanced)
            decoded.extend(decoded_clahe)

        # ==========================================================
        # 🧩 6. Resultados finales
        # ==========================================================
        if not decoded:
            raise HTTPException(status_code=404, detail="No se detectó ningún código de barras en la imagen.")

        seen = set()
        for d in decoded:
            code = d.data.decode("utf-8")
            if code not in seen:
                seen.add(code)
                results.append({"code": code, "type": d.type})

        return {"detected_barcodes": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando imagen: {e}")


# ==========================================================
# 🌐 2️⃣ Endpoint: Buscar producto por código (OpenFoodFacts)
# ==========================================================
@router.get("/lookup/{code}")
def lookup_barcode(code: str):
    """
    Busca información de un producto usando la API pública de OpenFoodFacts.
    Incluye datos nutricionales si están disponibles.
    """
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{code}.json"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Error al consultar OpenFoodFacts")

        data = response.json()

        if data.get("status") != 1:
            raise HTTPException(status_code=404, detail="Producto no encontrado en OpenFoodFacts")

        product = data.get("product", {})
        nutr = product.get("nutriments", {})

        return {
            "code": code,
            "product_name": product.get("product_name"),
            "brand": product.get("brands"),
            "categories": product.get("categories"),
            "description": product.get("generic_name", "Sin descripción"),
            "image": product.get("image_front_url"),
            "nutritional": {
                "calorias": nutr.get("energy-kcal"),
                "proteina": nutr.get("proteins"),
                "grasas": nutr.get("fat"),
                "carbohidratos": nutr.get("carbohydrates")
            },
            "source": "OpenFoodFacts"
        }

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Tiempo de espera agotado al consultar OpenFoodFacts")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la búsqueda: {e}")
