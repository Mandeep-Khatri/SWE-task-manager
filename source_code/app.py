from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional

from flask import Flask, flash, redirect, render_template, request, session, url_for

from task_manager import (
    PRIORITIES,
    STATUS_OPTIONS,
    get_next_task_id,
    hash_password,
    load_data,
    save_data,
)


app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def get_current_user_tasks(data: Dict) -> List[Dict]:
    username = session["username"]
    return data["users"][username]["tasks"]


def find_task_by_id(tasks: List[Dict], task_id: int) -> Optional[Dict]:
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("tasks"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        data = load_data()

        if not username:
            flash("Username is required.", "error")
        elif username in data["users"]:
            flash("Username already exists.", "error")
        elif not password:
            flash("Password is required.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            data["users"][username] = {"password_hash": hash_password(password), "tasks": []}
            save_data(data)
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        data = load_data()
        user = data["users"].get(username)

        if not user or user["password_hash"] != hash_password(password):
            flash("Invalid username or password.", "error")
        else:
            session["username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("tasks"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/tasks")
@login_required
def tasks():
    data = load_data()
    username = session["username"]
    all_tasks = list(get_current_user_tasks(data))

    keyword = request.args.get("keyword", "").strip().lower()
    priority = request.args.get("priority", "").strip().lower()
    status = request.args.get("status", "").strip().lower()

    if keyword:
        all_tasks = [
            task
            for task in all_tasks
            if keyword in task["title"].lower() or keyword in task["description"].lower()
        ]
    if priority in PRIORITIES:
        all_tasks = [task for task in all_tasks if task["priority"] == priority]
    if status in STATUS_OPTIONS:
        all_tasks = [task for task in all_tasks if task["status"] == status]

    all_tasks.sort(key=lambda t: t["id"])
    return render_template(
        "tasks.html",
        username=username,
        tasks=all_tasks,
        keyword=keyword,
        priority=priority,
        status=status,
        priorities=sorted(PRIORITIES),
        statuses=sorted(STATUS_OPTIONS),
    )


@app.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    data = load_data()
    tasks = get_current_user_tasks(data)

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "").strip().lower()

    if not title or not description:
        flash("Title and description are required.", "error")
    elif not validate_date(due_date):
        flash("Due date must be in YYYY-MM-DD format.", "error")
    elif priority not in PRIORITIES:
        flash("Invalid priority value.", "error")
    else:
        tasks.append(
            {
                "id": get_next_task_id(tasks),
                "title": title,
                "description": description,
                "due_date": due_date,
                "priority": priority,
                "status": "incomplete",
            }
        )
        save_data(data)
        flash("Task added.", "success")

    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/edit", methods=["POST"])
@login_required
def edit_task(task_id: int):
    data = load_data()
    tasks = get_current_user_tasks(data)
    task = find_task_by_id(tasks, task_id)

    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("tasks"))

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    priority = request.form.get("priority", "").strip().lower()
    status = request.form.get("status", "").strip().lower()

    if not title or not description:
        flash("Title and description are required.", "error")
    elif not validate_date(due_date):
        flash("Due date must be in YYYY-MM-DD format.", "error")
    elif priority not in PRIORITIES:
        flash("Invalid priority value.", "error")
    elif status not in STATUS_OPTIONS:
        flash("Invalid status value.", "error")
    else:
        task["title"] = title
        task["description"] = description
        task["due_date"] = due_date
        task["priority"] = priority
        task["status"] = status
        save_data(data)
        flash("Task updated.", "success")

    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id: int):
    data = load_data()
    tasks = get_current_user_tasks(data)
    task = find_task_by_id(tasks, task_id)

    if not task:
        flash("Task not found.", "error")
    else:
        tasks.remove(task)
        save_data(data)
        flash("Task deleted.", "success")

    return redirect(url_for("tasks"))


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_status(task_id: int):
    data = load_data()
    tasks = get_current_user_tasks(data)
    task = find_task_by_id(tasks, task_id)

    if not task:
        flash("Task not found.", "error")
    else:
        task["status"] = "complete" if task["status"] == "incomplete" else "incomplete"
        save_data(data)
        flash("Task status updated.", "success")

    return redirect(url_for("tasks"))


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5050)
