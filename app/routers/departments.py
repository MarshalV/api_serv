import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=schemas.Department, status_code=201)
def create_department(
    dept: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
):
    """
    Создать подразделение.

    - **name**: название (1–200 символов, пробелы по краям триммируются)
    - **parent_id**: id родительского подразделения (опционально)
    """
    logger.info("Создание подразделения: %s", dept.name)
    return crud.create_department(db, dept)


@router.post("/{id}/employees/", response_model=schemas.Employee, status_code=201)
def create_employee(
    id: int,
    emp: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
):
    """
    Создать сотрудника в подразделении.

    - **id**: id подразделения (404 если не найдено)
    - **full_name**: полное имя (1–200 символов)
    - **position**: должность (1–200 символов)
    - **hired_at**: дата найма (опционально)
    """
    logger.info("Создание сотрудника в подразделении %s: %s", id, emp.full_name)
    return crud.create_employee(db, id, emp)


@router.get("/{id}")
def get_department(
    id: int,
    depth: int = Query(default=1, ge=1, le=5, description="Глубина вложенных подразделений (1–5)"),
    include_employees: bool = Query(default=True, description="Включать список сотрудников"),
    db: Session = Depends(get_db),
):
    """
    Получить подразделение с деревом дочерних и сотрудниками.

    - **depth**: глубина вложенности (по умолчанию 1, максимум 5)
    - **include_employees**: включать ли сотрудников в ответ
    """
    logger.info("Получение подразделения %s (depth=%s, employees=%s)", id, depth, include_employees)
    db_dept = crud.get_department(db, id)
    if not db_dept:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")
    return crud.get_department_tree(db, db_dept, depth, include_employees)


@router.patch("/{id}", response_model=schemas.Department)
def update_department(
    id: int,
    dept_update: schemas.DepartmentUpdate,
    db: Session = Depends(get_db),
):
    """
    Переместить / переименовать подразделение.

    - **name**: новое название (опционально)
    - **parent_id**: новый родитель (опционально; null — сделать корневым)

    Возвращает 400 при самоссылке, 409 при попытке создать цикл в дереве.
    """
    logger.info("Обновление подразделения %s: %s", id, dept_update)
    updated = crud.update_department(db, id, dept_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")
    return updated


@router.delete("/{id}", status_code=204)
def delete_department(
    id: int,
    mode: str = Query(..., pattern="^(cascade|reassign)$", description="cascade | reassign"),
    reassign_to_department_id: Optional[int] = Query(
        default=None, description="Обязателен при mode=reassign"
    ),
    db: Session = Depends(get_db),
):
    """
    Удалить подразделение.

    - **mode=cascade**: удалить подразделение вместе со всеми дочерними и сотрудниками
    - **mode=reassign**: перевести сотрудников в `reassign_to_department_id`, дочерние
      подразделения поднять на уровень выше, затем удалить
    """
    logger.info("Удаление подразделения %s (mode=%s)", id, mode)
    success = crud.delete_department(db, id, mode, reassign_to_department_id)
    if not success:
        raise HTTPException(status_code=404, detail="Подразделение не найдено")
    return None
