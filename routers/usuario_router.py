from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from model.database import SessionLocal, Usuario, GeneroEnum, EstadoEnum
from datetime import date, datetime

router = APIRouter()

# Dependency para inyectar sesión DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 📥 Modelo de entrada
class UsuarioCreate(BaseModel):
    user_id: int
    nombre: str
    apellido: str
    email: EmailStr
    foto_perfil: Optional[str] = None
    genero: Optional[GeneroEnum] = GeneroEnum.otro
    fecha_nacimiento: Optional[str] = None
    telefono: Optional[str] = None
    estado: Optional[EstadoEnum] = EstadoEnum.activo

# 📤 Modelo de salida
class UsuarioResponse(BaseModel):
    id: int
    user_id: int
    nombre: str
    apellido: str
    email: str
    foto_perfil: Optional[str]
    genero: str
    fecha_nacimiento: date | None
    telefono: Optional[str]
    fecha_registro: datetime
    estado: str

    class Config:
        from_attributes  = True

# ✅ 1. Crear perfil
@router.post("/usuario/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(Usuario).filter(Usuario.user_id == usuario.user_id).first()
    if existente:
        raise HTTPException(status_code=400, detail="Perfil ya existe para este user_id")

    nuevo = Usuario(**usuario.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ✅ 2. Obtener perfil por user_id
@router.get("/usuario/{user_id}", response_model=UsuarioResponse)
def obtener_usuario(user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.user_id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# ✅ 3. Obtener varios usuarios por lista de user_ids (IN)
@router.get("/usuarios/", response_model=List[UsuarioResponse])
def obtener_usuarios_por_ids(ids: List[int] = [], db: Session = Depends(get_db)):
    if not ids:
        raise HTTPException(status_code=400, detail="Debes enviar una lista de IDs")
    usuarios = db.query(Usuario).filter(Usuario.user_id.in_(ids)).all()
    return usuarios

# ✅ 4. Actualizar perfil
@router.put("/usuario/{user_id}", response_model=UsuarioResponse)
def actualizar_usuario(user_id: int, datos: UsuarioCreate, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.user_id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for key, value in datos.dict(exclude_unset=True).items():
        setattr(usuario, key, value)

    db.commit()
    db.refresh(usuario)
    return usuario

# ✅ 5. Eliminar perfil
@router.delete("/usuario/{user_id}")
def eliminar_usuario(user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.user_id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
    return {"detail": "Usuario eliminado correctamente"}
