import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import and_, update, delete
from sqlalchemy.orm import Session

from app import models, schemas

logger = logging.getLogger(__name__)



def get_department(db: Session, department_id: int) -> Optional[models.Department]:
    """Возвращает подразделение по id или None."""
    return db.query(models.Department).filter(models.Department.id == department_id).first()


def create_department(db: Session, dept: schemas.DepartmentCreate) -> models.Department:
    """
    Создаёт новое подразделение.
    Проверяет существование родителя и уникальность имени в пределах родителя.
    """
    if dept.parent_id is not None:
        parent = get_department(db, dept.parent_id)
        if not parent:
            logger.error("Родительский отдел не найден: %s", dept.parent_id)
            raise HTTPException(status_code=404, detail="Родительский отдел не найден")

    # уникальность name внутри одного parent
    existing = db.query(models.Department).filter(
        and_(
            models.Department.parent_id == dept.parent_id,
            models.Department.name == dept.name.strip(),
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Подразделение с таким названием уже существует в данном родителе",
        )

    db_dept = models.Department(name=dept.name.strip(), parent_id=dept.parent_id)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    logger.info("Подразделение создано: id=%s", db_dept.id)
    return db_dept


def get_department_tree(
    db: Session,
    dept: models.Department,
    depth: int,
    include_employees: bool,
) -> dict:
    """
    Рекурсивно строит дерево подразделения до указанной глубины.
    Сотрудники сортируются по full_name.
    """
    result: dict = {
        "id": dept.id,
        "name": dept.name,
        "parent_id": dept.parent_id,
        "created_at": dept.created_at,
    }

    if include_employees:
        result["employees"] = sorted(
            [schemas.Employee.model_validate(e) for e in dept.employees],
            key=lambda x: x.full_name,
        )
    else:
        result["employees"] = []

    if depth > 0:
        result["children"] = [
            get_department_tree(db, child, depth - 1, include_employees)
            for child in dept.children
        ]
    else:
        result["children"] = []

    return result


def is_descendant(db: Session, potential_parent_id: int, target_id: int) -> bool:
    """
    Проверяет, является ли potential_parent_id потомком target_id.
    Используется для защиты от циклов в дереве.
    """
    if potential_parent_id == target_id:
        return True
    dept = get_department(db, potential_parent_id)
    if not dept or dept.parent_id is None:
        return False
    return is_descendant(db, dept.parent_id, target_id)


def update_department(
    db: Session,
    dept_id: int,
    dept_update: schemas.DepartmentUpdate,
) -> Optional[models.Department]:
    """
    Обновляет поля подразделения.
    Защищает от самоссылки и циклов в дереве (409 Conflict).
    """
    db_dept = get_department(db, dept_id)
    if not db_dept:
        return None

    if "parent_id" in dept_update.model_fields_set:
        new_parent_id = dept_update.parent_id
        
        if new_parent_id is not None:
            logger.info("Подразделение %s перемещено в подразделение %s", dept_id, new_parent_id)

            if new_parent_id == dept_id:
                raise HTTPException(
                    status_code=400, detail="Нельзя назначить подразделение родителем самого себя"
                )

            logger.info("Новый родительский отдел найден: id=%s", new_parent_id)
            if not get_department(db, new_parent_id):
                raise HTTPException(status_code=404, detail="Новый родительский отдел не найден")
            logger.info("Подразделение %s является потомком подразделения %s", dept_id, new_parent_id)

            if is_descendant(db, new_parent_id, dept_id):
                raise HTTPException(
                    status_code=409,
                    detail="Нельзя переместить подразделение внутрь своего собственного поддерева",
                )
        db_dept.parent_id = new_parent_id

    if dept_update.name is not None:
        logger.info("Подразделение обновлено: id=%s name=%s", db_dept.id, dept_update.name)
        db_dept.name = dept_update.name.strip()

    db.commit()
    db.refresh(db_dept)
    logger.info("Подразделение обновлено: id=%s", db_dept.id)
    return db_dept


def delete_department(
    db: Session,
    dept_id: int,
    mode: str,
    reassign_to: Optional[int] = None,
) -> bool:
    """
    Удаляет подразделение в режиме cascade или reassign.

    cascade  — рекурсивно удаляет всех сотрудников и дочерние подразделения.
    reassign — переводит сотрудников в reassign_to, дочерние отделы поднимаются
               на уровень удалённого родителя.
    """
    db_dept = get_department(db, dept_id)
    if not db_dept:
        logger.error("Подразделение не найдено: id=%s", dept_id)
        return False

    if mode == "cascade":
        db.delete(db_dept)
        logger.info("Подразделение удалено: id=%s", db_dept.id)

    elif mode == "reassign":
        if not reassign_to:
            raise HTTPException(
                status_code=400,
                detail="reassign_to_department_id обязателен при mode=reassign",
            )
        target = get_department(db, reassign_to)
        if not target:
            raise HTTPException(
                status_code=404,
                detail=f"Отдел для переноса сотрудников не найден: id={reassign_to}",
            )

        # 1. Переносим сотрудников в целевой отдел
        db.execute(
            update(models.Employee)
            .where(models.Employee.department_id == dept_id)
            .values(department_id=reassign_to)
        )
        logger.info("Сотрудники отдела %s перенесены в отдел %s", dept_id, reassign_to)

        # 2. Поднимаем дочерние отделы на уровень выше
        db.execute(
            update(models.Department)
            .where(models.Department.parent_id == dept_id)
            .values(parent_id=db_dept.parent_id)
        )
        logger.info("Дочерние отделы отдела %s подняты на уровень выше", dept_id)

        # 3. Флашим UPDATE-ы в БД (всё ещё в транзакции)
        db.flush()
        logger.info("UPDATE-ы в БД флашены")

        # 4. Удаляем отдел напрямую через SQL (не через ORM,
        #    чтобы не сработал cascade="all, delete-orphan")
        db.execute(
            delete(models.Department)
            .where(models.Department.id == dept_id)
        )
        logger.info("Отдел %s удален", dept_id)

    db.commit()
    logger.info("Подразделение удалено: id=%s mode=%s", dept_id, mode)
    return True


def create_employee(
    db: Session, dept_id: int, emp: schemas.EmployeeCreate
) -> models.Employee:
    """
    Создаёт сотрудника в указанном подразделении.
    Возвращает 404, если подразделение не найдено.
    """
    db_dept = get_department(db, dept_id)
    if not db_dept:
        logger.error("Подразделение не найдено: id=%s", dept_id)
        raise HTTPException(status_code=404, detail="Подразделение не найдено")

    db_emp = models.Employee(**emp.model_dump(), department_id=dept_id)
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    logger.info("Сотрудник создан: id=%s dept_id=%s", db_emp.id, dept_id) 
    return db_emp
