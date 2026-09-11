# Tailscale To-Do App

A localized, offline-first To-Do application running on Arch Linux with a FastAPI backend and a Progressive Web App (PWA) frontend. Works on Arch Linux, iOS, and iPadOS.

## Architecture

- **Backend**: FastAPI + SQLAlchemy + SQLite + APScheduler
- **Frontend**: Single-file HTML/JS with Tailwind CSS + Alpine.js
- **Networking**: Tailscale secure mesh VPN
- **Offline**: `localStorage` caching with automatic resynchronization

---

## Prerequisites

- Arch Linux server (or any machine where you can run Python)
- Tailscale installed on all devices (server + clients)
- librewolf (or any modern browser) on client devices

---

## Installation

### 1. Clone or copy the project

```bash
mkdir -p ~/todo-app
# Copy main.py, static/index.html, and requirements.txt into ~/todo-app/
```

### 2. Set up Python virtual environment

```bash
cd ~/todo-app
python3 -m venv venv
source venv/bin/activate
venv/bin/pip install fastapi uvicorn apscheduler pydantic
```

### 3. Run the server

```bash
# Method A: Interactive (stops when terminal closes)
venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

# Method B: Background (recommended)
setsid venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 < /dev/null > /tmp/todo-server.log 2>&1 &

# Verify it's running
curl -s http://localhost:8000/api/todos
# Output: []
```

### 4. Tailscale setup

On your Arch server:

```bash
tailscale up --advertise-routes=127.0.0.1/8
```

Find your server's Tailscale IP or MagicDNS:

```bash
tailscale ip
# Example output: 100.xx.xx.xx  arch-server (100.xx.xx.xx)
```

The app will be accessible at `http://arch-server:8000` via MagicDNS, or `http://100.xx.xx.xx:8000` via IP.

---

## Using the App

### On iOS & iPadOS

1. Ensure Tailscale is active on your iPhone/iPad and connected to your Tailnet
2. Open librewolf and go to `http://arch-server:8000`
3. Tap **Share** → **Add to Home Screen**
4. The app installs as a native-like icon on your home screen

**Features**:
- Add tasks with optional "Repeat daily (6:00 AM)" flag
- Tasks auto-reset every day at 6:00 AM via APScheduler
- Works offline: changes are cached in `localStorage` and synced when back online
- Connection status indicator (green = Synced, red = Offline)

### On Arch Linux Laptop

1. Ensure Tailscale is active
2. Open librewolf (or Chromium/Firefox) at `http://arch-server:8000`
3. Save as web app bookmark or use "Install this site as app" feature

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/todos` | Retrieve all todos |
| `POST` | `/api/sync` | Sync todos from client (creates/updates DB) |
| `DELETE` | `/api/todos/{id}` | Delete a todo by ID |

---

## How It Works

### Backend (`main.py`)

- **SQLite** database (`todos.db`) persists data locally
- **APScheduler** job runs daily at 06:00 AM to reset recurring tasks (`completed = 0 WHERE is_recurring = 1`)
- `POST /api/sync` uses `INSERT ... ON CONFLICT(id) DO UPDATE` for upsert behavior
- CORS allows all Tailscale origins (`allow_origins=["*"]`)

### Frontend (`static/index.html`)

- **Alpine.js** (`x-data`, `x-model`, `x-for`, etc.) for reactivity
- **Tailwind CSS** via CDN for styling
- **`localStorage`** caches todos locally
- `init()` sets up online/offline event listeners
- `sync()` posts todos to `/api/sync` every 10s when online
- Adds "6 AM" badge on recurring tasks

### Offline Behavior

1. User adds/edits/deletes tasks → immediately saved to `localStorage` + UI updated
2. If online, `sync()` immediately posts changes to server
3. If offline, changes remain in `localStorage`
4. Every 10s, app checks `navigator.onLine` and auto-syncs when connection restores

---

## Project Structure

```
todo-app/
├── main.py          # FastAPI backend
├── static/
│   └── index.html   # PWA frontend
├── venv/            # Python virtual environment
├── todos.db         # SQLite database (created automatically)
└── tmp/todo-server.log  # Server log output
```

---

## Development

To modify the backend:

```bash
source venv/bin/activate
# Edit main.py
venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

To modify the frontend:

1. Edit `static/index.html`
2. Changes are served instantly since StaticFiles mounts the directory

---

## Troubleshooting

- **Can't connect**: Verify Tailscale is `up` on all devices: `tailscale status`
- **API returns 404**: Ensure you're at `http://<tailscale-ip-or-hostname>:8000`, not just the IP without the port
- **Todos not syncing**: Check server log `cat /tmp/todo-server.log` and browser console for errors
- **Recurring tasks not resetting**: Ensure APScheduler job was created at startup (check `scheduler.start()` in main.py)