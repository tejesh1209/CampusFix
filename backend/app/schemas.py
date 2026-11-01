from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from .models import Role, Status, Priority

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    department: str | None = Field(default=None, max_length=120)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: Role
    department: str | None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class ComplaintCreate(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=10, max_length=5000)
    category: str = Field(min_length=2, max_length=80)
    location: str = Field(min_length=2, max_length=180)
    priority: Priority = Priority.medium

class ComplaintUpdate(BaseModel):
    status: Status | None = None
    priority: Priority | None = None
    assigned_to_id: int | None = None

class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    category: str
    location: str
    priority: Priority
    status: Status
    reporter_id: int
    assigned_to_id: int | None
    created_at: datetime
    updated_at: datetime
    reporter: UserOut
    assignee: UserOut | None
