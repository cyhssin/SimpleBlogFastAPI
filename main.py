from fastapi.security import OAuth2PasswordBearer
from app.jwt_utils import verify_access_token
from fastapi import FastAPI, Depends, status, HTTPException, Path
from sqlalchemy.orm import Session
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from app import schemas, crud
from app.database import get_db, engine, Base
from utils import send_verification_email
from app.jwt_utils import create_access_token

# Initialize tables when starting up
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blog API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = verify_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users", response_model=list[schemas.UserOut], tags=["user"])
def list_all_users(current_user: schemas.UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admins only")
    return crud.get_all_users(db)

@app.get("/profile", response_model=schemas.UserOut, tags=["user"])
def get_current_user_profile(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("session")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["user"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db, user)
    if not new_user:
        raise HTTPException(status_code=400, detail="User creation failed")
    token = crud.generate_email_verification_token(new_user.email)
    send_verification_email(new_user.email, token)
    return new_user

@app.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    email = crud.verify_email_verification_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_email_verified = True
    db.commit()
    return {"msg": "Email verified successfully"}

@app.post("/login", tags=["user"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logout", tags=["user"])
def logout():
    response = JSONResponse(content={"msg": "Logout successful"})
    response.delete_cookie(key="session")
    return response

@app.delete("/users/{user_id}", status_code=204, tags=["user"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

@app.patch("/users/{user_id}/deactivate", response_model=schemas.UserOut, tags=["user"])
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users/change-password", tags=["user"])
def change_password(
    req: schemas.PasswordChangeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_username(db, current_user.username)
    if not user or not crud.pwd_context.verify(req.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    user.hashed_password = crud.pwd_context.hash(req.new_password)
    db.commit()
    return {"msg": "Password changed successfully"}

@app.get("/", response_model=list[schemas.PostOut], tags=["blog"])
def get_all_posts(db: Session = Depends(get_db)):
    return crud.get_all_posts(db=db)

@app.post("/posts", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED, tags=["blog"])
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    new_post = crud.create_post(db=db, post=post)
    if not new_post:
        raise HTTPException(status_code=400, detail="Post creation failed")
    return new_post

@app.get("/posts/{post_id}", response_model=schemas.PostOut, tags=["blog"])
def get_post(post_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    post = crud.get_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.patch("/posts/{post_id}", response_model=schemas.PostOut, tags=["blog"])
def update_post(
    post_id: int,
    post_update: schemas.PostUpdate,
    db: Session = Depends(get_db),
):
    updated_post = crud.update_post(db=db, post_id=post_id, post_update=post_update)
    if not updated_post:
        raise HTTPException(status_code=400, detail="Update failed")
    return updated_post

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["blog"])
def delete_post(post_id: int, db: Session = Depends(get_db)):
    if not crud.delete_post(db=db, post_id=post_id):
        raise HTTPException(status_code=404, detail="Post not found")

@app.patch("/users/{user_id}", response_model=schemas.UserOut, tags=["blog"])
def update_user_profile(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
):
    updated_user = crud.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user
