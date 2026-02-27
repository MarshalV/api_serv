from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import List, Optional


class DepartmentBase(BaseModel):
    """Базовые поля подразделения (общие для Create и Response)."""

    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:

        """
        Проверка на пустое поле name
        *cls - класс
        *v - значение
        """

        v = v.strip()
        if not v:
            raise ValueError("Имя не может быть пустым")
        return v


class DepartmentCreate(DepartmentBase):
    """Схема создания подразделения."""
    pass


class DepartmentUpdate(BaseModel):
    """Схема частичного обновления подразделения."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Имя не может быть пустым")
        return v


class EmployeeBase(BaseModel):
    """Базовые поля сотрудника (общие для Create и Response)."""

    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: Optional[date] = None

    @field_validator("full_name", "position")
    @classmethod
    def field_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Поле не может быть пустым")
        return v


class EmployeeCreate(EmployeeBase):
    """Схема создания сотрудника."""
    pass


class Employee(EmployeeBase):
    """Схема ответа для сотрудника."""

    id: int
    department_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class Department(DepartmentBase):
    """Схема ответа для подразделения."""

    id: int
    created_at: datetime
    employees: List[Employee] = []
    children: List["Department"] = []

    model_config = {"from_attributes": True}


Department.model_rebuild()
