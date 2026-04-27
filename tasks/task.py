import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect
from datetime import timedelta

aplikace = Flask(__name__)
aplikace.secret_key = "super_secure_password_lol5"
aplikace.permanent_session_lifetime = timedelta(days=7)


def get_conn():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    
    # table users

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # table tasks

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id_task INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT
        )
    """)
    
    # table for connecting tasks and users, without this you basicly could only had one task assinged to one user

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tasks (
            id_user_task INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            id_task INTEGER NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,

            FOREIGN KEY (id_user) REFERENCES users(id),
            FOREIGN KEY (id_task) REFERENCES tasks(id_task)
        )
    """)

    conn.commit()
    conn.close()


def add_test_users():
    conn = get_conn()

    admin = conn.execute(
        "SELECT id FROM users WHERE name = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        conn.execute(
            "INSERT INTO users (name, password) VALUES (?, ?)",
            ("admin", "1234")
        )

    test = conn.execute(
        "SELECT id FROM users WHERE name = ?",
        ("test",)
    ).fetchone()

    if not test:
        conn.execute(
            "INSERT INTO users (name, password) VALUES (?, ?)",
            ("test", "1234")
        )

    conn.commit()
    conn.close()


def duplicitaJmen(name):
    conn = get_conn()
    existing_user = conn.execute(
        "SELECT name FROM users WHERE name = ?",
        (name,)
    ).fetchone()
    conn.close()
    return existing_user


@aplikace.route("/")
def index():
    return render_template("index.html")


@aplikace.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "missing data"}), 400

    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return jsonify({"success": False, "message": "missing name or password"}), 400

    conn = get_conn()

    user = conn.execute(
        "SELECT * FROM users WHERE name = ?",
        (name,)
    ).fetchone()

    conn.close()

    if not user:
        return jsonify({"success": False, "message": "user not existings"}), 401

    if user["password"] != password:
        return jsonify({"success": False, "message": "wrong password"}), 401

    session.permanent = True
    session["prihlasen"] = True
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return jsonify({
        "success": True,
        "message": f"Success, Welcome:  {name}"
    })


@aplikace.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "GET":
        return render_template("registration.html")

    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Chybí data"}), 400

    name = data.get("name")
    password = data.get("password")
    password2 = data.get("password2")

    if not name or not password or not password2:
        return jsonify({"success": False, "message": "missing name or password"}), 400

    if password != password2:
        return jsonify({"success": False, "message": "passwords dont match"}), 400

    if duplicitaJmen(name):
        return jsonify({"success": False, "message": "name already taken"}), 400

    conn = get_conn()

    conn.execute(
        "INSERT INTO users (name, password) VALUES (?, ?)",
        (name, password)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Users registred"
    })


@aplikace.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@aplikace.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login?msg=Not logged")

    conn = get_conn()

    tasks = conn.execute("""
        SELECT 
            user_tasks.id_user_task,
            tasks.title,
            tasks.description,
            user_tasks.completed
        FROM user_tasks
        JOIN tasks ON user_tasks.id_task = tasks.id_task
        WHERE user_tasks.id_user = ?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "profile.html",
        user_name=session["user_name"],
        tasks=tasks
    )


@aplikace.route("/task-completed", methods=["PUT"])
def task_completed():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "not logged"}), 401

    data = request.get_json()

    id_user_task = data.get("id_user_task")
    completed = data.get("completed")

    if id_user_task is None or completed is None:
        return jsonify({"success": False, "message": "Missing data"}), 400

    conn = get_conn()

    conn.execute("""
        UPDATE user_tasks
        SET completed = ?
        WHERE id_user_task = ? AND id_user = ?
    """, (1 if completed else 0, id_user_task, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Task changed"
    })


@aplikace.route("/Admin", methods=["GET", "POST"])
def Admin():
    if "user_id" not in session:
        return redirect("/login?msg=you need to log in first")

    if session["user_name"] != "admin":
        return redirect("/login?msg=not an admin")

    if request.method == "GET":
        return render_template("Admin.html")

    data = request.get_json()

    user = data.get("user")
    task = data.get("task")
    desc = data.get("desc")

    if not user or not task:
        return jsonify({"success": False, "message": "task or user missing"}), 400

    conn = get_conn()

    selected_user = conn.execute(
        "SELECT id FROM users WHERE name = ?",
        (user,)
    ).fetchone()

    if not selected_user:
        conn.close()
        return jsonify({"success": False, "message": "users not existing"}), 404

    cursor = conn.execute(
        "INSERT INTO tasks (title, description) VALUES (?, ?)",
        (task, desc)
    )

    id_task = cursor.lastrowid

    conn.execute(
        "INSERT INTO user_tasks (id_user, id_task) VALUES (?, ?)",
        (selected_user["id"], id_task)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Task was addes to user"
    })


if __name__ == "__main__":
    init_db()
    add_test_users()
    aplikace.run(debug=True)