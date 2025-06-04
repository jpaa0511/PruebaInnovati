from pydantic import BaseModel, EmailStr
from typing import Any, Optional

class EmailProcessRequest(BaseModel):
    email_content: str
    user_email: EmailStr

class EmailResponse(BaseModel):
    message: str
    result: dict