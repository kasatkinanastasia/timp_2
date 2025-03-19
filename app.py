from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('todo.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создание таблицы задач, если она не существует
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Функция для получения списка задач
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return tasks

@app.route('/')
def index():
    tasks = get_tasks()  # Получаем список задач
    print(tasks)  # Отладочный вывод
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    task_title = request.form['task']
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (title) VALUES (?)', (task_title,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))  # перенаправление обратно на страницу с задачами

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        if title:
            conn.execute('UPDATE tasks SET title = ? WHERE id = ?', (title, task_id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    conn.close()
    return render_template('edit.html', task=task)

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()

    if task:
        completed = not task['completed']
        conn.execute('UPDATE tasks SET completed = ? WHERE id = ?', (completed, task_id))
        conn.commit()

    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # Инициализация базы данных при запуске приложения
    app.run(debug=True)
