from pydantic import EmailStr, Field

from app.schemas.base import CamelModel


class SignupRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=64)


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"


class WithdrawRequest(CamelModel):
    password: str = Field(min_length=1, max_length=64)
