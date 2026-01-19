from sqlmodel import SQLModel, Field
from pydantic import BaseModel
import datetime


class CurrencyModel(SQLModel, table=True):
    __tablename__ = "currencies"
    id: int | None = Field(primary_key=True)
    name: str
    unit: int
    char_code: str
    num_code: int
    rate: float
    date: datetime.date

class CurrencyCreate(BaseModel):
    name: str
    unit: int
    char_code: str
    num_code: int
    rate: float
    date: datetime.date

class CurrencyUpdate(CurrencyCreate):
    name: str = None
    unit: int = None
    char_code: str = None
    num_code: int = None
    rate: float = None
    date: datetime.date = None

class Currency(CurrencyCreate):
    id: int