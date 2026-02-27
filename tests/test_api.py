import pytest


def test_create_department(client):

    """POST /departments/ — создание подразделения."""

    response = client.post("/departments/", json={"name": "Backend"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Backend"
    assert data["parent_id"] is None


def test_create_child_department(client):

    """POST /departments/ — создание дочернего подразделения."""

    parent = client.post("/departments/", json={"name": "Backend"})
    assert parent.status_code == 201
    parent_id = parent.json()["id"]

    response = client.post("/departments/", json={"name": "Python", "parent_id": parent_id})
    assert response.status_code == 201
    assert response.json()["parent_id"] == parent_id


def test_no_cycle(client):

    """PATCH /departments/{id} — попытка создать цикл возвращает 409."""

    resp_a = client.post("/departments/", json={"name": "A"})
    assert resp_a.status_code == 201
    id_a = resp_a.json()["id"]

    resp_b = client.post("/departments/", json={"name": "B", "parent_id": id_a})
    assert resp_b.status_code == 201
    id_b = resp_b.json()["id"]

    resp_cycle = client.patch(f"/departments/{id_a}", json={"parent_id": id_b})
    assert resp_cycle.status_code == 409


def test_cascade_delete_removes_children(client):

    """DELETE ?mode=cascade — дочерние подразделения и сотрудники удаляются."""

    parent = client.post("/departments/", json={"name": "Root"})
    assert parent.status_code == 201
    parent_id = parent.json()["id"]

    child = client.post("/departments/", json={"name": "Child", "parent_id": parent_id})
    assert child.status_code == 201
    child_id = child.json()["id"]

    # Удаляем родителя каскадно
    resp = client.delete(f"/departments/{parent_id}?mode=cascade")
    assert resp.status_code == 204

    # Дочерний отдел тоже должен быть удалён
    assert client.get(f"/departments/{child_id}").status_code == 404


def test_reassign_invalid_target(client):
    
    """DELETE ?mode=reassign — 404 если целевой отдел не существует."""

    dept = client.post("/departments/", json={"name": "ToDelete"})
    assert dept.status_code == 201
    dept_id = dept.json()["id"]

    resp = client.delete(f"/departments/{dept_id}?mode=reassign&reassign_to_department_id=9999")
    assert resp.status_code == 404



def test_duplicate_name_in_same_parent(client):
    """POST /departments/ — дублирующееся name в одном родителе возвращает 400."""

    resp1 = client.post("/departments/", json={"name": "Backend"})
    assert resp1.status_code == 201

    resp2 = client.post("/departments/", json={"name": "Backend"})
    assert resp2.status_code == 400


def test_create_employee_in_nonexistent_dept(client):

    
    """POST /departments/{id}/employees/ — 404 если отдел не найден."""
    resp = client.post("/departments/9999/employees/", json={"full_name": "Ivan", "position": "Dev"})
    assert resp.status_code == 404
