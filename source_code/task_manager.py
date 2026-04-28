import getpass
import hashlib
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional


BASE_DIR = os.path.dirname(__file__)
BUNDLED_DATA_FILE = os.path.abspath(
    os.path.join(BASE_DIR, "..", "data", "task_manager_data.json")
)
SERVERLESS_DATA_FILE = "/tmp/task_manager_data.json"


def resolve_data_file() -> str:
    env_file = os.getenv("TASK_MANAGER_DATA_FILE")
    if env_file:
        return env_file
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # Serverless environments allow writes in /tmp only.
        return SERVERLESS_DATA_FILE
    if not os.access(os.path.dirname(BUNDLED_DATA_FILE), os.W_OK):
        return SERVERLESS_DATA_FILE
    return BUNDLED_DATA_FILE


DATA_FILE = resolve_data_file()
PRIORITIES = {"low", "medium", "high"}
STATUS_OPTIONS = {"incomplete", "complete"}


def ensure_data_file() -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        if DATA_FILE != BUNDLED_DATA_FILE and os.path.exists(BUNDLED_DATA_FILE):
            shutil.copyfile(BUNDLED_DATA_FILE, DATA_FILE)
        else:
            save_data({"users": {}})


def load_data() -> Dict:
    ensure_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict) -> None:
    global DATA_FILE
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return
    except OSError:
        if DATA_FILE == SERVERLESS_DATA_FILE:
            raise

    # Fallback for read-only filesystems.
    DATA_FILE = SERVERLESS_DATA_FILE
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def prompt_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Value cannot be empty.")


def prompt_date(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")


def prompt_priority(prompt: str, allow_empty: bool = False) -> Optional[str]:
    while True:
        value = input(prompt).strip().lower()
        if allow_empty and not value:
            return None
        if value in PRIORITIES:
            return value
        print("Invalid priority. Choose low, medium, or high.")


def prompt_status(prompt: str, allow_empty: bool = False) -> Optional[str]:
    while True:
        value = input(prompt).strip().lower()
        if allow_empty and not value:
            return None
        if value in STATUS_OPTIONS:
            return value
        print("Invalid status. Choose incomplete or complete.")


def create_account(data: Dict) -> None:
    print("\n=== Create Account ===")
    username = prompt_non_empty("Choose a username: ")
    if username in data["users"]:
        print("Username already exists. Try logging in.")
        return

    password = getpass.getpass("Choose a password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("Passwords do not match.")
        return
    if not password:
        print("Password cannot be empty.")
        return

    data["users"][username] = {"password_hash": hash_password(password), "tasks": []}
    save_data(data)
    print("Account created successfully.")


def login(data: Dict) -> Optional[str]:
    print("\n=== Login ===")
    username = prompt_non_empty("Username: ")
    password = getpass.getpass("Password: ")

    user = data["users"].get(username)
    if not user:
        print("User not found.")
        return None
    if user["password_hash"] != hash_password(password):
        print("Incorrect password.")
        return None
    print(f"Welcome, {username}.")
    return username


def get_next_task_id(tasks: List[Dict]) -> int:
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


def display_tasks(tasks: List[Dict]) -> None:
    if not tasks:
        print("No tasks found.")
        return

    print("\n--- Tasks ---")
    for task in tasks:
        print(
            f"[{task['id']}] {task['title']} | Priority: {task['priority'].title()} | "
            f"Status: {task['status'].title()} | Due: {task['due_date']}"
        )
        print(f"    Description: {task['description']}")


def find_task_by_id(tasks: List[Dict], task_id: int) -> Optional[Dict]:
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def add_task(data: Dict, username: str) -> None:
    print("\n=== Add Task ===")
    tasks = data["users"][username]["tasks"]
    new_task = {
        "id": get_next_task_id(tasks),
        "title": prompt_non_empty("Task title: "),
        "description": prompt_non_empty("Task description: "),
        "due_date": prompt_date("Due date (YYYY-MM-DD): "),
        "priority": prompt_priority("Priority (low/medium/high): "),
        "status": "incomplete",
    }
    tasks.append(new_task)
    save_data(data)
    print("Task added.")


def edit_task(data: Dict, username: str) -> None:
    print("\n=== Edit Task ===")
    tasks = data["users"][username]["tasks"]
    display_tasks(tasks)
    if not tasks:
        return

    try:
        task_id = int(input("Enter task ID to edit: ").strip())
    except ValueError:
        print("Invalid task ID.")
        return

    task = find_task_by_id(tasks, task_id)
    if not task:
        print("Task not found.")
        return

    print("Press Enter to keep the current value.")
    title = input(f"Title [{task['title']}]: ").strip()
    description = input(f"Description [{task['description']}]: ").strip()
    due_date = input(f"Due date [{task['due_date']}] (YYYY-MM-DD): ").strip()
    priority = prompt_priority(
        f"Priority [{task['priority']}] (low/medium/high): ", allow_empty=True
    )
    status = prompt_status(
        f"Status [{task['status']}] (incomplete/complete): ", allow_empty=True
    )

    if title:
        task["title"] = title
    if description:
        task["description"] = description
    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
            task["due_date"] = due_date
        except ValueError:
            print("Invalid date entered. Keeping previous due date.")
    if priority:
        task["priority"] = priority
    if status:
        task["status"] = status

    save_data(data)
    print("Task updated.")


def delete_task(data: Dict, username: str) -> None:
    print("\n=== Delete Task ===")
    tasks = data["users"][username]["tasks"]
    display_tasks(tasks)
    if not tasks:
        return

    try:
        task_id = int(input("Enter task ID to delete: ").strip())
    except ValueError:
        print("Invalid task ID.")
        return

    task = find_task_by_id(tasks, task_id)
    if not task:
        print("Task not found.")
        return

    tasks.remove(task)
    save_data(data)
    print("Task deleted.")


def mark_complete(data: Dict, username: str) -> None:
    print("\n=== Mark Task Complete ===")
    tasks = data["users"][username]["tasks"]
    incomplete_tasks = [t for t in tasks if t["status"] == "incomplete"]
    display_tasks(incomplete_tasks)
    if not incomplete_tasks:
        return

    try:
        task_id = int(input("Enter task ID to mark complete: ").strip())
    except ValueError:
        print("Invalid task ID.")
        return

    task = find_task_by_id(tasks, task_id)
    if not task:
        print("Task not found.")
        return

    task["status"] = "complete"
    save_data(data)
    print("Task marked as complete.")


def search_tasks(data: Dict, username: str) -> None:
    print("\n=== Search Tasks ===")
    keyword = prompt_non_empty("Enter keyword: ").lower()
    tasks = data["users"][username]["tasks"]
    results = [
        task
        for task in tasks
        if keyword in task["title"].lower() or keyword in task["description"].lower()
    ]
    display_tasks(results)


def filter_tasks(data: Dict, username: str) -> None:
    print("\n=== Filter Tasks ===")
    print("1. Filter by priority")
    print("2. Filter by status")
    choice = input("Choose filter type: ").strip()

    tasks = data["users"][username]["tasks"]
    if choice == "1":
        priority = prompt_priority("Priority (low/medium/high): ")
        results = [task for task in tasks if task["priority"] == priority]
        display_tasks(results)
    elif choice == "2":
        status = prompt_status("Status (incomplete/complete): ")
        results = [task for task in tasks if task["status"] == status]
        display_tasks(results)
    else:
        print("Invalid choice.")


def user_menu(data: Dict, username: str) -> None:
    while True:
        print(f"\n=== Task Manager ({username}) ===")
        print("1. Add task")
        print("2. View all tasks")
        print("3. Edit task")
        print("4. Delete task")
        print("5. Mark task complete")
        print("6. Search tasks")
        print("7. Filter tasks")
        print("8. Logout")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            add_task(data, username)
        elif choice == "2":
            display_tasks(data["users"][username]["tasks"])
        elif choice == "3":
            edit_task(data, username)
        elif choice == "4":
            delete_task(data, username)
        elif choice == "5":
            mark_complete(data, username)
        elif choice == "6":
            search_tasks(data, username)
        elif choice == "7":
            filter_tasks(data, username)
        elif choice == "8":
            print("Logged out.")
            return
        else:
            print("Invalid menu option.")


def main() -> None:
    while True:
        data = load_data()
        print("\n=== Python Task Manager ===")
        print("1. Create account")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter choice: ").strip()
        if choice == "1":
            create_account(data)
        elif choice == "2":
            username = login(data)
            if username:
                user_menu(data, username)
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid menu option.")


if __name__ == "__main__":
    main()
