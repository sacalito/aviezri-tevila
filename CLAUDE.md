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

## API Reference

**Base URL**: `http://<raspberry-pi-ip>:5000`

### Authentication

All endpoints (except `GET /`) require a Bearer token in the `Authorization` header.

```
Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX
```

**Error responses when auth fails:**
- Missing token: `401 {"message": "No token provided"}`
- Invalid token: `401 {"message": "Invalid token"}`

---

### `GET /`

Returns the web UI (no auth required).

---

### `GET /api/status`

Get system status and both relay states.

**Request:**
```bash
curl -X GET http://localhost:5000/api/status \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX"
```

**Response:**
```json
{
  "status": "online",
  "time": "2026-03-25 17:34:00",
  "heating": "on",
  "filtering": "off"
}
```

---

### `POST /relay/on`

Turn a relay ON.

**Request:**
```bash
curl -X POST http://localhost:5000/relay/on \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"relay": "heating"}'
```

**Body:** `{"relay": "heating"}` or `{"relay": "filtering"}`

**Response:**
```json
{"success": true, "relay": "heating", "state": "on"}
```

**Errors:**
- `400` — Unknown relay name

---

### `POST /relay/off`

Turn a relay OFF.

**Request:**
```bash
curl -X POST http://localhost:5000/relay/off \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"relay": "filtering"}'
```

**Body:** `{"relay": "heating"}` or `{"relay": "filtering"}`

**Response:**
```json
{"success": true, "relay": "filtering", "state": "off"}
```

---

### `POST /relay/status`

Check a single relay's current state.

**Request:**
```bash
curl -X POST http://localhost:5000/relay/status \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"relay": "heating"}'
```

**Body:** `{"relay": "heating"}` or `{"relay": "filtering"}`

**Response:**
```json
{"relay": "heating", "state": "off"}
```

---

### `POST /hours`

Get schedule entries. Send empty body `{}` for all, or filter by relay.

**Request (all schedules):**
```bash
curl -X POST http://localhost:5000/hours \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Request (filter by relay):**
```bash
curl -X POST http://localhost:5000/hours \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"relay": "heating"}'
```

**Response:**
```json
{
  "hours": [
    {
      "id": 1,
      "relay": "heating",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "17:00"
    },
    {
      "id": 2,
      "relay": "filtering",
      "day": "Monday",
      "start_time": "08:00",
      "end_time": "20:00"
    }
  ]
}
```

Results are sorted by relay, then day (Monday-Sunday, Holiday), then start_time.

---

### `POST /add_hours`

Add a schedule entry for a relay.

**Request:**
```bash
curl -X POST http://localhost:5000/add_hours \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"relay": "heating", "day": "Monday", "start_time": "09:00", "end_time": "17:00"}'
```

**Body:**
| Field | Required | Values |
|-------|----------|--------|
| `relay` | yes | `"heating"` or `"filtering"` |
| `day` | yes | `"Monday"`, `"Tuesday"`, `"Wednesday"`, `"Thursday"`, `"Friday"`, `"Saturday"`, `"Sunday"`, `"Holiday"` |
| `start_time` | yes | `"HH:MM"` or `"HH:MM:SS"` |
| `end_time` | yes | `"HH:MM"` or `"HH:MM:SS"` |

**Response:**
```json
{
  "success": true,
  "hours": {
    "id": 1,
    "relay": "heating",
    "day": "Monday",
    "start_time": "09:00",
    "end_time": "17:00"
  }
}
```

**Errors:**
- `400` — Missing required fields
- `400` — Unknown relay name

---

### `POST /delete_hours`

Delete a schedule entry by ID.

**Request:**
```bash
curl -X POST http://localhost:5000/delete_hours \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"hour_id": 1}'
```

**Response:**
```json
{"success": true, "message": "Hours with ID 1 deleted"}
```

**Errors:**
- `404` — No hours found with that ID

---

### `GET /dates`

Get all special dates (holidays).

**Request:**
```bash
curl -X GET http://localhost:5000/dates \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX"
```

**Response:**
```json
{
  "dates": [
    {"id": 1, "date": "2026-04-01"},
    {"id": 2, "date": "2026-12-25"}
  ]
}
```

---

### `POST /add_date`

Add a special date. If the date already exists, returns the existing entry.

**Request:**
```bash
curl -X POST http://localhost:5000/add_date \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-04-01"}'
```

**Response:**
```json
{"success": true, "date": {"id": 1, "date": "2026-04-01"}}
```

**Errors:**
- `400` — Missing date field

---

### `POST /delete_date`

Delete a special date by ID.

**Request:**
```bash
curl -X POST http://localhost:5000/delete_date \
  -H "Authorization: Bearer FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX" \
  -H "Content-Type: application/json" \
  -d '{"date_id": 1}'
```

**Response:**
```json
{"success": true, "message": "Date with ID 1 deleted"}
```

**Errors:**
- `404` — No date found with that ID

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
