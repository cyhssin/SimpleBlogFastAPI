from fastapi import FastAPI, Depends, status, HTTPException, Path
from sqlalchemy.orm import Session
from app import schemas, crud
from app.database import get_db, engine, Base

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

# Initialize tables when starting up
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blog API")

@app.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
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
    return new_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response = JSONResponse(content={"msg": "Login successful", "username": user.username})
    response.set_cookie(key="session", value=user.username, httponly=True)
    return response

@app.post("/logout")
def logout():
    response = JSONResponse(content={"msg": "Logout successful"})
    response.delete_cookie(key="session")
    return response

@app.get("/", response_model=list[schemas.PostOut])
async def get_all_posts(db: Session = Depends(get_db)):
    return crud.get_all_posts(db=db)

@app.post("/posts", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    new_post = crud.create_post(db=db, post=post)
    if not new_post:
        raise HTTPException(status_code=400, detail="Post creation failed")
    return new_post

@app.get("/posts/{post_id}", response_model=schemas.PostOut)
async def get_post(post_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    post = crud.get_post(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.patch("/posts/{post_id}", response_model=schemas.PostOut)
async def update_post(
    post_id: int,
    post_update: schemas.PostUpdate,
    db: Session = Depends(get_db)
):
    updated_post = crud.update_post(db=db, post_id=post_id, post_update=post_update)
    if not updated_post:
        raise HTTPException(status_code=400, detail="Update failed")
    return updated_post

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    if not crud.delete_post(db=db, post_id=post_id):
        raise HTTPException(status_code=404, detail="Post not found")