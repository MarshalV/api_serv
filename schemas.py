from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from typing import List, Optional

class DepartmentBase(BaseModel):
    """
    базовая модель отдела
    """
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

class DepartmentCreate(DepartmentBase):
    """
    создание отдела
    """
    pass

class DepartmentUpdate(BaseModel):
    """
    обновление отдела
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty")
        return v

class EmployeeBase(BaseModel):
    """
    базовая модель сотрудника
    """
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: Optional[date] = None

    @field_validator("full_name", "position")
    @classmethod
    def field_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v

class EmployeeCreate(EmployeeBase):
    """
    создание сотрудника
    """
    pass

class Employee(EmployeeBase):
    """
    модель сотрудника
    """
    id: int
    department_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class Department(DepartmentBase):
    """
    модель отдела
    """
    id: int
    created_at: datetime
    employees: List[Employee] = []
    children: List["Department"] = []

    model_config = {"from_attributes": True}

Department.model_rebuild()
