from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str

class PostBase(BaseModel):
    title: str
    content: str
    is_published: bool = True

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None

class PostOut(PostBase):
    id: int
    
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None