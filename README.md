# Task Manager Web App (Python + Flask)

A simple, clean Task Manager application built for a software engineering class project.  
It supports user authentication and full task management with permanent JSON file storage.

## Live Project Scope

This project satisfies the assignment requirements for:
- User login system (signup, login, logout)
- Task management (add, view, edit, delete, mark complete)
- Search and filtering (keyword, priority, status)
- Persistent data storage using JSON

## Tech Stack

- Python 3
- Flask
- HTML (Jinja templates)
- CSS
- JSON file storage

## Project Structure

```text
SWE/
├── source_code/
│   ├── app.py
│   ├── task_manager.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── tasks.html
│   └── static/
│       └── styles.css
├── data/
│   └── task_manager_data.json
├── requirements.txt
└── README.md
```

## Features

### Authentication
- Create account (username + password)
- Login
- Logout
- Passwords are stored as SHA-256 hashes

### Task Operations
Each task includes:
- Title
- Description
- Due date
- Priority (`low`, `medium`, `high`)
- Status (`incomplete`, `complete`)

Supported actions:
- Add task
- View tasks
- Edit task
- Delete task
- Mark complete/incomplete

### Search and Filter
- Search tasks by keyword (title/description)
- Filter by priority
- Filter by completion status

### Persistent Data Storage
- Data file: `data/task_manager_data.json`
- Data loads from JSON when app handles requests
- File is updated after every data change

## Setup and Run

From the project root (`SWE/`):

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

2. Install dependencies:
   ```bash
   .venv/bin/python -m pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   .venv/bin/python source_code/app.py
   ```

4. Open in browser:
   - `http://127.0.0.1:5050`

## Notes

- Port `5050` is used because `5000` may be occupied on some macOS setups.
- This is a development server (Flask built-in server), suitable for class/demo use.

## Suggested Test Checklist

- Create a new account
- Login with valid credentials
- Add task with valid fields
- Edit existing task
- Mark task complete
- Filter by `high` priority
- Search by keyword
- Delete task
- Restart app and verify data persisted

## Author

- Mandeep Khatri
