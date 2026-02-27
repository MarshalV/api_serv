from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, func
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для моделей SQLAlchemy"""
    pass


class Department(Base):
    """
    Модель подразделения.

    Поля:
        id: первичный ключ
        name: название (не пустое)
        parent_id: FK на родительское подразделение (self-reference)
        created_at: дата создания

    Связи:
        parent: родительское подразделение
        children: дочерние подразделения (cascade delete)
        employees: сотрудники (cascade delete)
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    parent = relationship("Department", remote_side=[id], back_populates="children")
    children = relationship(
        "Department",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    employees = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan",
    )


class Employee(Base):
    """
    Модель сотрудника.

    Поля:
        id: первичный ключ
        department_id: FK на подразделение
        full_name: полное имя (не пустое)
        position: должность (не пустая)
        hired_at: дата найма (опционально)
        created_at: дата создания
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    full_name = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    hired_at = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    department = relationship("Department", back_populates="employees")
