from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class ContactBase(BaseModel):
    first_name: str
    second_name: str
    email: EmailStr  # Use EmailStr for validation
    phone: str
    birthdate: date
    additional_data: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class Contact(ContactBase):
    id: int

    class Config:
        from_attributes = True  # Allow ORM-style attribute fetching


class UserCreate(BaseModel):
    username: str
    email: EmailStr  # Ensure email is validated
    password: str  # Password is kept here but not in the response


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr  # Use EmailStr for validation

    class Config:
        from_attributes = True  # Allow ORM-mode serialization


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr  # EmailStr for validation
