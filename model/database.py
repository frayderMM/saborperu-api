from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


from sqlalchemy import (
    Column, Integer, String, Date, Enum, ForeignKey, Text, TIMESTAMP, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

# 🔹 Reemplaza con tus credenciales RDS:
DB_USER = "admin"
DB_PASSWORD = "123456789"
DB_HOST = "saborperu-db.czh1rhqevenw.us-east-1.rds.amazonaws.com"
DB_NAME = "saborperudb"

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# 🧱 Modelo User que refleja tu tabla "users"
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    perfil = relationship("Usuario", uselist=False, back_populates="user")

# 🔹 Enumeraciones
class GeneroEnum(str, enum.Enum):
    masculino = "masculino"
    femenino = "femenino"
    otro = "otro"

class EstadoEnum(str, enum.Enum):
    activo = "activo"
    inactivo = "inactivo"

# 🔹 Modelo de la tabla 'usuario' (perfil personal)
class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    foto_perfil = Column(Text, nullable=True)
    genero = Column(Enum(GeneroEnum), default=GeneroEnum.otro)
    fecha_nacimiento = Column(Date, nullable=True)
    telefono = Column(String(20), nullable=True)
    fecha_registro = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    estado = Column(Enum(EstadoEnum), default=EstadoEnum.activo)

    # Relación con User
    user = relationship("User", back_populates="perfil")