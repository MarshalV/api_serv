from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional
import schemas, crud
from models import Base
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:testadmin@localhost:5433/main_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():

    """
    Получение сессии базы данных
    """
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="D&E API")

@app.post("/departments/", response_model=schemas.Department)
def create_department(dept: schemas.DepartmentCreate, db: Session = Depends(get_db)):
    """
    создание отдела
    **dept** - данные отдела
    **db** - сессия базы данных 
    """
    logger.info(f"Создание отдела: {dept.name}")
    return crud.create_department(db, dept)

@app.post("/departments/{id}/employees/", response_model=schemas.Employee)
def create_employee(id: int, emp: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    """
    создание сотрудника
    **id** - id отдела
    **emp** - данные сотрудника
    **db** - сессия базы данных
    """
    logger.info(f"Создание сотрудника в отделе {id}: {emp.full_name}")
    return crud.create_employee(db, id, emp)

@app.get("/departments/{id}")
def get_department(
    id: int, 
    depth: int = Query(1, ge=1, le=5), 
    include_employees: bool = True, 
    db: Session = Depends(get_db)
):
    """
    получение отдела
    **id** - id отдела
    **depth** - глубина вложенности
    **include_employees** - включать сотрудников
    **db** - сессия базы данных
    """
    logger.info(f"Получение отдела {id} с глубиной {depth} и сотрудниками {include_employees}")
    db_dept = crud.get_department(db, id)
    if not db_dept:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return crud.get_department_tree(db, db_dept, depth, include_employees)

@app.patch("/departments/{id}", response_model=schemas.Department)
def update_department(id: int, dept_update: schemas.DepartmentUpdate, db: Session = Depends(get_db)):
    """
    обновление отдела
    **id** - id отдела
    **dept_update** - данные отдела
    **db** - сессия базы данных
    """
    logger.info(f"Обновление отдела {id}: {dept_update.name}")
    updated = crud.update_department(db, id, dept_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return updated

@app.delete("/departments/{id}", status_code=204)
def delete_department(
    id: int, 
    mode: str = Query(..., pattern="^(cascade|reassign)$"),
    reassign_to_department_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    удаление отдела
    **id** - id отдела
    **mode** - режим удаления (cascade (удаление с подразделениями) или reassign (перенос сотрудников))
    **reassign_to_department_id** - id отдела, на который перенесутся сотрудники
    **db** - сессия базы данных
    """
    logger.info(f"Удаление отдела {id} в режиме {mode}")
    success = crud.delete_department(db, id, mode, reassign_to_department_id)
    if not success:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return None
