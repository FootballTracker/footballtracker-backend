from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from models.user import User 
from schemas import UserCreate, UserResponse, UserLogin, UserUpdate
from database.database import get_db_session
from utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


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
            detail="Username or email already exists",
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
        "email": new_user.email
    }


@router.post("/signin")
async def signin(user_data: UserLogin, db: AsyncSession = Depends(get_db_session)):

    stmt = select(User).where(
        or_(User.username == user_data.username, User.email == user_data.username)
    )


    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }


@router.post("/user_delete")
async def user_delete(user_data: UserLogin, db: AsyncSession = Depends(get_db_session)):
    
    stmt = select(User).where(User.id == user_data.user_id)

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # TO BE DECIDED IF MAKES SENSE
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user_id or password")


    await db.delete(user)
    await db.commit()

    return {"message": f"User {user.username} has been deleted successfully."}

@router.put("/update_user")
async def update_user(
        user_id: int,
        password: str,
        username: str | None = None,
        email: str | None = None,
        new_password: str | None = None,
        db: AsyncSession = Depends(get_db_session)
    ):

    # Fetch user by ID
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated = False

    # Handle username or email update
    if username or email:
        if not password or not verify_password(password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password for updating username/email")

        # Check for uniqueness if changing username/email
        if username and username != user.username:
            stmt = select(User).where(User.username == username)
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
            user.username = username
            updated = True

        if email and email != user.email:
            stmt = select(User).where(User.email == email)
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")
            user.email = email
            updated = True

    # Handle password update
    if new_password:
        if not password or not verify_password(password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password for updating password")
        user.password = hash_password(password)
        updated = True

    if not updated:
        return {"message": "No updates were made."}

    await db.commit()
    await db.refresh(user)

    return {"message": "User updated successfully."}