import tensorflow as tf
import numpy as np
from PIL import Image

# --- Cargar modelo y etiquetas ---
MODEL_PATH = "model/keras_model_v1.h5"
LABELS_PATH = "model/labels.txt"

model = tf.keras.models.load_model(MODEL_PATH)
with open(LABELS_PATH, "r", encoding="utf-8") as f:
    class_names = [line.strip() for line in f.readlines()]

def predict_image(image_path: str):
    """Clasifica una imagen y devuelve la etiqueta y la confianza."""
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    img_array = np.asarray(img, dtype=np.float32) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)
    index = np.argmax(predictions[0])
    confidence = float(predictions[0][index]) * 100.0

    return {
        "plato": class_names[index],
        "confianza": round(confidence, 2)
    }
