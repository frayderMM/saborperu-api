from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from model.database import SessionLocal, MealHistory, Usuario
from datetime import datetime, timedelta

# ===========================================================
# 🔹 Configuración inicial
# ===========================================================
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===========================================================
# 🔹 Función auxiliar para mapear user_id → usuario.id
# ===========================================================
def get_usuario_id(user_id: int, db: Session):
    usuario = db.query(Usuario).filter(Usuario.user_id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario.id

# ===========================================================
# 🔹 Promedio de nutrientes
# ===========================================================
@router.get("/average-nutrients/{user_id}")
def get_average_nutrients(user_id: int, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(user_id, db)

    result = (
        db.query(
            func.avg(MealHistory.calories).label("avg_calories"),
            func.avg(MealHistory.proteins).label("avg_proteins"),
            func.avg(MealHistory.fats).label("avg_fats"),
            func.avg(MealHistory.carbs).label("avg_carbs")
        )
        .filter(MealHistory.usuario_id == usuario_id)
        .first()
    )

    if not result or all(v is None for v in result):
        raise HTTPException(status_code=404, detail="Sin datos suficientes")

    return result._asdict()

# ===========================================================
# 🔹 Conteo de comidas por día (últimos 7 días)
# ===========================================================
@router.get("/meal-count/{user_id}")
def get_meal_count(user_id: int, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(user_id, db)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    data = (
        db.query(
            func.date(MealHistory.created_at).label("day"),
            func.count(MealHistory.id).label("count")
        )
        .filter(
            MealHistory.usuario_id == usuario_id,
            MealHistory.created_at >= seven_days_ago
        )
        .group_by(func.date(MealHistory.created_at))
        .order_by(func.date(MealHistory.created_at))
        .all()
    )

    if not data:
        raise HTTPException(status_code=404, detail="Sin registros de comidas recientes")

    return [{"day": str(row.day), "count": row.count} for row in data]

# ===========================================================
# 🔹 Platos más frecuentes
# ===========================================================
@router.get("/top-meals/{user_id}")
def get_top_meals(user_id: int, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(user_id, db)

    data = (
        db.query(
            MealHistory.meal_name,
            func.count(MealHistory.meal_name).label("count")
        )
        .filter(MealHistory.usuario_id == usuario_id)
        .group_by(MealHistory.meal_name)
        .order_by(func.count(MealHistory.meal_name).desc())
        .limit(5)
        .all()
    )

    if not data:
        raise HTTPException(status_code=404, detail="Sin registros de platos")

    return [{"meal_name": m.meal_name, "count": m.count} for m in data]

# ===========================================================
# 🔹 Estadísticas globales
# ===========================================================
@router.get("/global-stats")
def get_global_stats(db: Session = Depends(get_db)):
    total_meals = db.query(func.count(MealHistory.id)).scalar() or 0
    avg_calories = db.query(func.avg(MealHistory.calories)).scalar() or 0.0
    return {"total_meals": total_meals, "avg_calories": avg_calories}

# ===========================================================
# 🔹 Proporción de macronutrientes (% proteínas, grasas, carbos)
# ===========================================================
@router.get("/nutrient-ratio/{user_id}")
def get_nutrient_ratio(user_id: int, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(user_id, db)
    result = (
        db.query(
            func.avg(MealHistory.proteins).label("proteins"),
            func.avg(MealHistory.fats).label("fats"),
            func.avg(MealHistory.carbs).label("carbs")
        )
        .filter(MealHistory.usuario_id == usuario_id)
        .first()
    )

    if not result or (result.proteins is None):
        raise HTTPException(status_code=404, detail="Sin datos suficientes")

    total = (result.proteins or 0) + (result.fats or 0) + (result.carbs or 0)
    if total == 0:
        return {"proteins_pct": 0, "fats_pct": 0, "carbs_pct": 0}

    return {
        "proteins_pct": round((result.proteins / total) * 100, 2),
        "fats_pct": round((result.fats / total) * 100, 2),
        "carbs_pct": round((result.carbs / total) * 100, 2),
    }

# ===========================================================
# 🔹 Promedio de calorías por día (últimos 7 días)
# ===========================================================
@router.get("/weekly-calories/{user_id}")
def get_weekly_calories(user_id: int, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(user_id, db)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    data = (
        db.query(
            cast(func.date(MealHistory.created_at), Date).label("day"),
            func.avg(MealHistory.calories).label("avg_calories")
        )
        .filter(
            MealHistory.usuario_id == usuario_id,
            MealHistory.created_at >= seven_days_ago
        )
        .group_by(cast(func.date(MealHistory.created_at), Date))
        .order_by(cast(func.date(MealHistory.created_at), Date))
        .all()
    )

    if not data:
        raise HTTPException(status_code=404, detail="Sin datos de calorías recientes")

    return [{"day": str(row.day), "avg_calories": float(row.avg_calories)} for row in data]
