from pydantic import BaseModel, Field, EmailStr

class RegisterIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str
class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
class UserOut(BaseModel):
    id: int; display_name: str; email: str; role: str
    @classmethod
    def from_user(cls, u): 
        return cls(id=u.id, display_name=u.display_name, email=u.email, role=u.role)
class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut