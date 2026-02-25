from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


"""Базовый класс для моделей SQLAlchemy"""
class Base(DeclarativeBase):
	pass

class Department(Base):
    """
    модель отдела
    id: int - идентификатор отдела
    name: str - название отдела
    parent_id: int - идентификатор родительского отдела
    created_at: datetime - дата создания отдела
    parent: Department - родительский отдел
    employees: List[Employee] - список сотрудников
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    parent = relationship("Department", remote_side=[id], backref="children")
    employees = relationship("Employee", back_populates="department", cascade="all, delete-orphan")

class Employee(Base):
    """
    модель сотрудника
    id: int - идентификатор сотрудника
    department_id: int - идентификатор отдела
    full_name: str - полное имя сотрудника
    position: str - должность сотрудника
    hired_at: date - дата приема на работу
    created_at: datetime - дата создания сотрудника
    department: Department - отдел
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    hired_at = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    department = relationship("Department", back_populates="employees")
