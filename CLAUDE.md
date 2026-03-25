# Tevila Control System

Raspberry Pi 4 based system for controlling two relay modules (heating and filtering) for a tevila, with scheduled automation and a web UI.

## Running

```bash
cd /root/aviezri-tevila/app
pip install flask flask-sqlalchemy gpiozero apscheduler --break-system-packages
python3 main.py
```

Runs on `http://0.0.0.0:5000`. Must run with `debug=False` to avoid GPIO busy errors from Flask's reloader forking a second process.

## Hardware

- **Platform**: Raspberry Pi 4
- **Heating relay**: GPIO 24 (physical pin 18)
- **Filtering relay**: GPIO 23 (physical pin 16)
- GPIO numbering: BCM mode (gpiozero default)
- Relay logic is inverted: `LED.off()` = relay ON, `LED.on()` = relay OFF

## Project Structure

```
app/
  main.py           - Flask app entry point, scheduler setup
  routes.py         - All API endpoints
  relayControl.py   - GPIO relay control (gpiozero LED)
  database.py       - SQLAlchemy models (Hours, Dates) and CRUD functions
  api.py            - Bearer token auth decorator
  log_config.py     - Logging setup
  imports.py        - Shared imports (legacy)
  functions.py      - Empty utility module (legacy)
  templates/
    index.html      - Web UI (Alpine.js + Flatpickr)
  static/
    css/style.css   - Styling
    css/flatpickr.min.css
    js/alpine3.min.js
    js/flatpickr.js
  data/
    database/tevila.db  - SQLite database (auto-created)
    access.log          - Application log
```

## Database

SQLite at `app/data/database/tevila.db`.

**Hours table**: `id`, `relay` (heating/filtering), `day` (Monday-Sunday/Holiday), `start_time`, `end_time`

**Dates table**: `id`, `date` (YYYY-MM-DD) — special dates that use the "Holiday" schedule

## Scheduler

APScheduler runs every minute (`cron minute='*'`). For each relay, it checks if the current time falls within any schedule entry for that relay and day. If yes, turns relay ON. If no, turns relay OFF. Special dates in the Dates table override the weekday and use the "Holiday" schedule instead.

## API Endpoints

All protected endpoints require `Authorization: Bearer <token>` header.
Token: `FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX`

### Relay Control
- `POST /relay/on` — `{"relay": "heating"|"filtering"}` — Turn relay on
- `POST /relay/off` — `{"relay": "heating"|"filtering"}` — Turn relay off
- `POST /relay/status` — `{"relay": "heating"|"filtering"}` — Check relay state

### Status
- `GET /api/status` — System status with both relay states

### Schedule Management
- `POST /hours` — Get all hours (optional `{"relay": "heating"}` to filter)
- `POST /add_hours` — `{"relay": "heating", "day": "Monday", "start_time": "09:00", "end_time": "17:00"}`
- `POST /delete_hours` — `{"hour_id": 1}`

### Special Dates
- `GET /dates` — Get all special dates
- `POST /add_date` — `{"date": "2026-01-01"}`
- `POST /delete_date` — `{"date_id": 1}`

## Web UI

Alpine.js single-page app at `/`. Features:
- Live status display with relay state badges (green=on, red=off)
- ON / OFF / Toggle buttons for each relay
- Separate schedule panels for heating and filtering
- Flatpickr calendar for managing special dates (click to add, click red date to remove)

## Dependencies

- Flask
- Flask-SQLAlchemy
- gpiozero
- APScheduler
