from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from model.database import SessionLocal, User
from utils.auth_utils import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# ==============================
# 📦 Modelos de datos
# ==============================
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None

# ==============================
# 🔌 Conexión BD
# ==============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================
# 🧩 Registro de usuario
# ==============================
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")
    
    new_user = User(
        username=user.username,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "✅ Usuario creado con éxito", "user_id": new_user.id}

# ==============================
# 🔑 Login
# ==============================
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_token({"sub": db_user.username})
    
    return {
        "access_token": token,
        "username": db_user.username,
        "user_id": db_user.id  # ✅ Agrega esta línea
    }









# ==============================
# 📋 Listar usuarios
# ==============================
@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username} for u in users]

# ==============================
# 🔍 Obtener usuario por ID
# ==============================
@router.get("/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"id": user.id, "username": user.username}

# ==============================
# ✏️ Actualizar usuario
# ==============================
@router.put("/user/{user_id}")
def update_user(user_id: int, updated: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if updated.username:
        user.username = updated.username
    if updated.password:
        user.password = hash_password(updated.password)
    
    db.commit()
    db.refresh(user)
    return {"message": "✅ Usuario actualizado correctamente"}

# ==============================
# 🗑️ Eliminar usuario
# ==============================
@router.delete("/user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(user)
    db.commit()
    return {"message": "🗑️ Usuario eliminado correctamente"}
