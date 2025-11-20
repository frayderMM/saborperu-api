from pydantic import BaseModel
from datetime import datetime

class MealHistoryBase(BaseModel):
    meal_name: str
    method: str
    confidence: float | None = None
    calories: float | None = None
    proteins: float | None = None
    fats: float | None = None
    carbs: float | None = None
    image_url: str | None = None

class MealHistoryCreate(MealHistoryBase):
    usuario_id: int

class MealHistoryResponse(MealHistoryBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
