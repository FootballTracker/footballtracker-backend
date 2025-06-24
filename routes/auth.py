from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from models.user import User 
from schemas import UserCreate, UserResponse, UserLogin, UserUpdate
from database.database import get_db_session
from utils.security import hash_password, verify_password, create_access_token, get_current_user
from .. import schemas


@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db_session)):
    # Check if user or email already exists
    stmt = select(User).where(
        or_(User.username == user_data.username, User.email == user_data.email)
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário ou email já cadastrados",
        )

    hashed_pw = hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_pw,
        favorite_team=user_data.favorite_team,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "id":  new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "image": False
    }


@router.post("/signin", response_model=schemas.Token)
async def signin(user_data: UserLogin, db: AsyncSession = Depends(get_db_session)):
    if user_data.email:
        stmt = select(User).where(User.email == user_data.email)
    else:
        stmt = select(User).where(User.username == user_data.username)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=schemas.UserPublic)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/users/me", response_model=schemas.UserPublic)
async def update_user_profile(
    user_data: schemas.UserUpdate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    if not verify_password(user_data.current_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect current password")

    if user_data.username:
        current_user.username = user_data.username
    if user_data.email:
        current_user.email = user_data.email
    if user_data.new_password:
        current_user.password = hash_password(user_data.new_password)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_data: schemas.UserDelete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    if not verify_password(user_data.password, current_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    await db.delete(current_user)
    await db.commit()
    return None