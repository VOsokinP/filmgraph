from pydantic import BaseModel, EmailStr, Field, field_validator

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    recaptcha_token: str | None = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    firstName: str = Field(min_length=1, max_length=50)
    lastName: str = Field(min_length=1, max_length=50)
    recaptcha_token: str | None = None

    @field_validator("firstName", "lastName")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("password")
    @classmethod
    def within_bcrypt_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"must be at most {MAX_PASSWORD_BYTES} bytes; bcrypt silently ignores anything beyond"
            )
        return value


class CustomerOut(BaseModel):
    id: int
    firstName: str
    lastName: str
    email: EmailStr