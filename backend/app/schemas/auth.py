from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    recaptcha_token: str | None = None

class CustomerOut(BaseModel):
    id: int
    firstName: str
    lastName: str
    email: EmailStr