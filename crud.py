from sqlalchemy.orm import Session
import models, schemas
from fastapi import HTTPException
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)    


def get_department(db: Session, department_id: int):
    return db.query(models.Department).filter(models.Department.id == department_id).first()

def create_department(db: Session, dept: schemas.DepartmentCreate):
    # Проверяем существование родителя
    if dept.parent_id is not None:
        logger.info(f"ID родительского отдела: {dept.parent_id}")
        parent = get_department(db, dept.parent_id)
        if not parent:
            logger.error(f"Родительский отдел не найден: {dept.parent_id}")
            raise HTTPException(status_code=404, detail="Родительский отдел не найден")

    # Проверяем уникальность имени внутри родителя
    existing = db.query(models.Department).filter(
        and_(
            models.Department.parent_id == dept.parent_id,
            models.Department.name == dept.name.strip()
        )
    ).first()
    if existing:
        logger.error(f"Отдел с таким именем уже существует в этом родителе: {dept.name}")
        raise HTTPException(status_code=400, detail="Отдел с таким именем уже существует в этом родителе")
    
    db_dept = models.Department(name=dept.name.strip(), parent_id=dept.parent_id)

    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    logger.info(f"Отдел создан: {db_dept.id}")
    return db_dept

def get_department_tree(db: Session, dept: models.Department, depth: int, include_employees: bool):
    result = {
        "id": dept.id,
        "name": dept.name,
        "parent_id": dept.parent_id,
        "created_at": dept.created_at,
    }
    if include_employees:
        result["employees"] = sorted(
            [schemas.Employee.model_validate(e) for e in dept.employees],
            key=lambda x: x.full_name
        )
        logger.info(f"Найдено сотрудников: {len(dept.employees)}")
    
    if depth > 0:
        children = []
        for child in dept.children:
            children.append(get_department_tree(db, child, depth - 1, include_employees))
        result["children"] = children
        logger.info(f"Найдено дочерних отделов: {len(children)}")
    else:
        logger.info("Дочерние отделы не найдены")
        result["children"] = []
    
    return result

def is_descendant(db: Session, potential_parent_id: int, target_id: int) -> bool:
    logger.info(f"Проверка, является ли {potential_parent_id} потомком {target_id}")
    if potential_parent_id == target_id:
        logger.info(f"{potential_parent_id} является потомком {target_id}")
        return True
    dept = get_department(db, potential_parent_id)
    if not dept or dept.parent_id is None:
        logger.info(f"{potential_parent_id} не является потомком {target_id}")
        return False
    return is_descendant(db, dept.parent_id, target_id)

def update_department(db: Session, dept_id: int, dept_update: schemas.DepartmentUpdate):
    logger.info(f"Обновление отдела: {dept_id}")
    db_dept = get_department(db, dept_id)
    if not db_dept:
        logger.error(f"Отдел не найден: {dept_id}")
        return None
    
    if dept_update.parent_id is not None:
        if dept_update.parent_id == dept_id:
            logger.error(f"Нельзя сделать отдел своим родителем: {dept_id}")
            raise HTTPException(status_code=400, detail="Нельзя сделать отдел своим родителем")
        if is_descendant(db, dept_update.parent_id, dept_id):
            logger.error(f"Обнаружен цикл: Нельзя переместить отдел в свой собственный поддерево: {dept_id}")
            raise HTTPException(status_code=409, detail="Обнаружен цикл: Нельзя переместить отдел в свой собственный поддерево")

    if dept_update.name:
        logger.info(f"Обновление названия отдела: {dept_update.name}")
        db_dept.name = dept_update.name.strip()
    if dept_update.parent_id is not None:
        logger.info(f"Обновление родительского отдела: {dept_update.parent_id}")
        db_dept.parent_id = dept_update.parent_id
    
    db.commit()
    db.refresh(db_dept)
    logger.info(f"Отдел обновлен: {db_dept.id}")
    return db_dept

def delete_department(db: Session, dept_id: int, mode: str, reassign_to: int = None):
    logger.info(f"Удаление отдела: {dept_id}")
    db_dept = get_department(db, dept_id)
    if not db_dept:
        logger.error(f"Отдел не найден: {dept_id}")
        return False
    
    if mode == "cascade":
        db.delete(db_dept)
    elif mode == "reassign":
        if not reassign_to:
            logger.error(f"Не указан id отдела для переноса сотрудников: {dept_id}")
            raise HTTPException(status_code=400, detail="Не указан id отдела для переноса сотрудников")
        
        # Перенос сотрудников
        for emp in db_dept.employees:
            emp.department_id = reassign_to
        
        # Перенос подразделений
        for child in db_dept.children:
            child.parent_id = db_dept.parent_id
            
        db.delete(db_dept)
    else:
        logger.error(f"Неверный режим удаления: {mode}")
        raise HTTPException(status_code=400, detail="Неверный режим удаления")
    
    db.commit()
    logger.info(f"Отдел удален: {dept_id}")
    return True

def create_employee(db: Session, dept_id: int, emp: schemas.EmployeeCreate):
    logger.info(f"Создание сотрудника: {emp.full_name}")
    db_dept = get_department(db, dept_id)
    if not db_dept:
        logger.error(f"Отдел не найден: {dept_id}")
        raise HTTPException(status_code=404, detail="Отдел не найден")
    
    db_emp = models.Employee(**emp.model_dump(), department_id=dept_id)
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    logger.info(f"Сотрудник создан: {db_emp.id}")
    return db_emp
