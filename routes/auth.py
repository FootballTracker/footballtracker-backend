from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import user
from schemas import UserCreate, UserResponse
from database.database import get_db_session
from utils.security import hash_password

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db_session)):
    # Check if user or email already exists
    if db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")
    
    hashed_pw = hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_pw,
        favorite_team=user_data.favorite_team
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/signin")
def signin(user_data: UserCreate, db: Session = Depends(get_db_session)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return {"message": f"Welcome back, {user.username}!"}