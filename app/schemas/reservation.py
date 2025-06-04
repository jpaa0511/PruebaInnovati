from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

class ReservationBase(BaseModel):
    book_id: int
    user_email: EmailStr
    end_date: datetime

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(BaseModel):
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class ReservationInDBBase(ReservationBase):
    id: int
    start_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Reservation(ReservationInDBBase):
    pass