import pytest


def test_create_department(client):
    """
    Тестирование эндпоинта /departments/
    """
    # Создание отдела
    response = client.post("/departments/", json={"name": "Backend"})
    # Проверка, что отдел создан
    assert response.status_code == 200
    # Получение данных отдела
    data = response.json()
    # Проверка имени отдела
    assert data["name"] == "Backend"
    # Проверка, что у отдела нет родителя
    assert data["parent_id"] is None


def test_create_child_department(client):
    """
    Тестирование эндпоинта /departments/
    """
    # Создание родительского отдела
    parent = client.post("/departments/", json={"name": "Backend"})
    assert parent.status_code == 200
    parent_id = parent.json()["id"]

    # Создание дочернего отдела
    response = client.post("/departments/", json={"name": "Python", "parent_id": parent_id})
    assert response.status_code == 200
    assert response.json()["parent_id"] == parent_id


def test_no_cycle(client):
    """
    Тестирование эндпоинта /departments/
    """
    # Создание отдела
    resp_a = client.post("/departments/", json={"name": "A"})
    assert resp_a.status_code == 200
    id_a = resp_a.json()["id"]

    # Создание дочернего отдела
    resp_b = client.post("/departments/", json={"name": "B", "parent_id": id_a})
    assert resp_b.status_code == 200
    id_b = resp_b.json()["id"]

    # Проверка на цикл
    resp_cycle = client.patch(f"/departments/{id_a}", json={"parent_id": id_b})
    assert resp_cycle.status_code == 409
