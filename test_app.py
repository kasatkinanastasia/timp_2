import pytest
import sqlite3
from flask import Flask
from app import app as flask_app, init_db, get_db_connection


# Фикстура для тестового приложения
@pytest.fixture
def app():
    """Создаем тестовое приложение с базой данных в памяти"""
    flask_app.config['TESTING'] = True
    flask_app.config['DATABASE'] = 'file:testdb?mode=memory&cache=shared'
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Отключаем CSRF для тестов

    # Создаем соединение с базой данных
    conn = sqlite3.connect(flask_app.config['DATABASE'], uri=True)
    conn.row_factory = sqlite3.Row
    flask_app.get_db_connection = lambda: conn

    with flask_app.app_context():
        init_db()  # Инициализируем базу данных

    yield flask_app

    # Закрываем соединение после тестов
    conn.close()


# Фикстура для тестового клиента
@pytest.fixture
def client(app):
    """Создаем тестовый клиент"""
    return app.test_client()


def print_test_result(test_name, passed):
    """Выводит результат теста в удобном формате"""
    status = "✓ УСПЕХ" if passed else "✗ ОШИБКА"
    print(f"\n=== {test_name} ===")
    print(f"{status} - Тест {'пройден' if passed else 'не пройден'}")


def test_index(client):
    """Тест главной страницы"""
    test_name = "Тестирование главной страницы"
    try:
        response = client.get('/')
        assert response.status_code == 200
        assert b'Tasks' in response.data
        print_test_result(test_name, True)
    except AssertionError:
        print_test_result(test_name, False)
        raise


def test_add_task(client, app):
    """Тест добавления задачи"""
    test_name = "Тестирование добавления задачи"
    try:
        response = client.post('/add', data={'task': 'New Task'}, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            conn = get_db_connection()
            tasks = conn.execute('SELECT * FROM tasks').fetchall()
            assert len(tasks) == 1
            assert tasks[0]['title'] == 'New Task'
            assert tasks[0]['completed'] == 0

        print_test_result(test_name, True)
    except AssertionError:
        print_test_result(test_name, False)
        raise


def test_edit_task(client, app):
    """Тест редактирования задачи"""
    test_name = "Тестирование редактирования задачи"
    try:
        # Сначала добавляем задачу
        client.post('/add', data={'task': 'Initial Task'})

        with app.app_context():
            conn = get_db_connection()
            task = conn.execute('SELECT id FROM tasks').fetchone()
            task_id = task['id']

        # Редактируем задачу
        response = client.post(f'/edit/{task_id}', data={'title': 'Updated Task'}, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            updated_task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
            assert updated_task['title'] == 'Updated Task'

        print_test_result(test_name, True)
    except AssertionError:
        print_test_result(test_name, False)
        raise


def test_delete_task(client, app):
    """Тест удаления задачи"""
    test_name = "Тестирование удаления задачи"
    try:
        # Сначала добавляем задачу
        client.post('/add', data={'task': 'Task to delete'})

        with app.app_context():
            conn = get_db_connection()
            task = conn.execute('SELECT id FROM tasks').fetchone()
            task_id = task['id']

        # Удаляем задачу
        response = client.get(f'/delete/{task_id}', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            tasks = conn.execute('SELECT * FROM tasks').fetchall()
            assert len(tasks) == 0

        print_test_result(test_name, True)
    except AssertionError:
        print_test_result(test_name, False)
        raise


def test_complete_task(client, app):
    """Тест отметки выполнения задачи"""
    test_name = "Тестирование отметки выполнения задачи"
    try:
        # Сначала добавляем задачу
        client.post('/add', data={'task': 'Task to complete'})

        with app.app_context():
            conn = get_db_connection()
            task = conn.execute('SELECT * FROM tasks').fetchone()
            task_id = task['id']
            initial_completed = task['completed']

        # Изменяем статус задачи
        response = client.post(f'/complete/{task_id}', follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            updated_task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
            assert updated_task['completed'] != initial_completed

        print_test_result(test_name, True)
    except AssertionError:
        print_test_result(test_name, False)
        raise


def test_edit_nonexistent_task(client):
    """Тест редактирования несуществующей задачи"""
    test_name = "Тестирование редактирования несуществующей задачи"
    try:
        response = client.post('/edit/999', data={'title': 'New Title'}, follow_redirects=True)
        assert response.status_code == 200
        print_test_result(test_name, True)
    except AssertionError:
        print_test_result(test_name, False)
        raise


def test_delete_nonexistent_task(client):
    """Тест удаления несуществующей задачи"""
    test_name = "Тестирование удаления несуществующей задачи"
    try:
        response = client.get('/delete/999', follow_redirects=True)
        assert response.status_code == 200
        print_test_result(test_name, True)
    except AssertionError:
        print_test_result(test_name, False)
        raise


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("ЗАПУСК ТЕСТОВ СЕРВЕРНОГО ПРИЛОЖЕНИЯ")
    print("=" * 50 + "\n")

    # Запускаем тесты через pytest
    pytest.main(["-v", __file__])