import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# Allow requests from all Tailscale devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "todos.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                is_recurring INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

init_db()

class TodoItem(BaseModel):
    id: str
    title: str
    completed: bool
    is_recurring: bool
    updated_at: Optional[str] = None

# Scheduled Task: Reset recurring tasks every day at 6:00 AM
def process_recurring_tasks():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Un-complete recurring tasks so they reappear daily
        cursor.execute("UPDATE todos SET completed = 0 WHERE is_recurring = 1")
        conn.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(process_recurring_tasks, 'cron', hour=6, minute=0)
scheduler.start()

@app.get("/api/todos", response_model=List[TodoItem])
def get_todos():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute("SELECT id, title, completed, is_recurring, updated_at FROM todos").fetchall()
        return [
            {
                "id": r["id"], 
                "title": r["title"], 
                "completed": bool(r["completed"]), 
                "is_recurring": bool(r["is_recurring"]),
                "updated_at": r["updated_at"]
            } 
            for r in rows
        ]

@app.post("/api/sync")
def sync_todos(client_todos: List[TodoItem]):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        for todo in client_todos:
            cursor.execute("""
                INSERT INTO todos (id, title, completed, is_recurring, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    completed=excluded.completed,
                    is_recurring=excluded.is_recurring,
                    updated_at=CURRENT_TIMESTAMP
            """, (todo.id, todo.title, int(todo.completed), int(todo.is_recurring)))
        conn.commit()
    return get_todos()

@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: str):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
    return {"status": "success"}

# Serve Frontend static assets
app.mount("/", StaticFiles(directory="static", html=True), name="static")