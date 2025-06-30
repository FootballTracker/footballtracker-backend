# footballtracker-backend/utils/security.py

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.database import get_db_session
from models.user import User

# --- CRIPTOGRAFIA DA SENHA ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- LÓGICA DO TOKEN JWT ---
SECRET_KEY = "d83ac036380dc75d9639cf4d37a2376b15b845dc4d8a8e045185f60de6a53a11"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Token válido por 24 horas

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- DEPENDÊNCIA PARA OBTER O USUÁRIO LOGADO ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/signin")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    stmt = select(User).where(User.email == user_identifier)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user