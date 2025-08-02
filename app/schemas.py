from pydantic import BaseModel

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
    title: str | None = None
    content: str | None = None
    is_published: bool | None = None

class PostOut(PostBase):
    id: int

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None
