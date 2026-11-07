import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db, UserModel, User

# ==============================================================================
# 2. Configuración de Seguridad
# ==============================================================================
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production-super-secret-key-coworking")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Unificado a 60 minutos 

# ==============================================================================
# 3. Configuración de Cifrado y OAuth2
# ==============================================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Jerarquía de Roles
ROLE_HIERARCHY = {
    "user": 1,
    "admin": 2,
    "superadmin": 3
}

# ==============================================================================
# 4. Modelos de Datos Pydantic
# ==============================================================================
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = "user"

class UserInDB(BaseModel):
    email: str
    full_name: str
    role: str = "user"
    hashed_password: str

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: Optional[str] = "user"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# ==============================================================================
# 5 & 6. Verificación y Generación de Hashes de Contraseñas
# ==============================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña ingresada con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash seguro mediante bcrypt."""
    return pwd_context.hash(password)

# ==============================================================================
# 7. Crear el Token de Acceso JWT
# ==============================================================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea y firma un JWT con fecha de expiración en UTC.
    Contiene información del usuario: sub (email), role y exp.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==============================================================================
# 8. Identificar al Usuario Autenticado
# ==============================================================================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Extrae y valida el JWT enviado en el header Authorization: Bearer <token>.
    Recupera al usuario correspondiente de la base de datos PostgreSQL.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=payload.get("role", "user"))
    except JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# ==============================================================================
# 9. Controlar los Permisos Según el Rol (RBAC)
# ==============================================================================
def require_role(required_role: str) -> Callable:
    """
    Controla el acceso según la jerarquía de roles:
      - user: Nivel 1 (Usuario básico)
      - admin: Nivel 2 (Administrador)
      - superadmin: Nivel 3 (Administrador principal)
    Si el rol del usuario no tiene el nivel mínimo, retorna 403 Forbidden.
    """
    async def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{required_role}' or higher required. Current role: '{current_user.role}'"
            )
        return current_user

    return role_checker
