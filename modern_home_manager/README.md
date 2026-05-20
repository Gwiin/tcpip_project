# Modern Home Manager

`modern_home_manager` is an independent Flask dashboard that reads and writes the project MySQL schema used by `main.py`.

## Structure

- `app.py`: Flask page and JSON API.
- `database.py`: MySQL connection, dashboard queries, Pico frame ingestion.
- `mysql_queries.sql`: Paste-ready MySQL schema, seed data, indexes, and a dashboard check query.
- `simulator.py`: Writes Pico simulator frames into MySQL.
- `init_db.py`: Checks MySQL connectivity.
- `templates/dashboard.html`: Dashboard page.
- `static/script.js`: Fetches API data and handles room selection, toggles, and browser location.
- `static/styles.css`: Dashboard styling.

## MySQL Setup

Paste this file directly into MySQL:

```text
modern_home_manager/mysql_queries.sql
```

It creates `Home_Manager`, the root project tables, `MODERN_BROWSER_LOCATION`, seed data, and useful indexes.

## Environment

The app reads these variables. If omitted, it uses the defaults below.

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=Home_Manager
```

## Run

Install dependencies:

```powershell
python -m pip install -r modern_home_manager/requirements.txt
```

Check the MySQL connection:

```powershell
python -m modern_home_manager.init_db
```

Start the Flask server:

```powershell
python -m modern_home_manager.app
```

Open:

```text
http://127.0.0.1:5173
```

## Pico Simulator

Write one simulated Pico batch:

```powershell
python -m modern_home_manager.simulator --once
```

Or keep writing values every 5 seconds:

```powershell
python -m modern_home_manager.simulator --interval 5
```

The simulator inserts rows into:

- `SENSOR_READING`
- `ACTUATOR_STATE_LOG`

Refresh the dashboard to see the updated values.

## API

- `GET /api/dashboard`: Full dashboard payload from MySQL.
- `GET /api/rooms/<room_id>`: One room with its sensors and actuators.
- `POST /api/actuators/<actuator_id>/toggle`: Insert latest actuator state. Body: `{"active": true}`.
- `POST /api/location`: Store browser geolocation in `MODERN_BROWSER_LOCATION`.
- `POST /api/pico/ingest`: Store one Pico JSON frame.
- `GET /api/health`: MySQL connectivity check.

## Tests

```powershell
python -m unittest discover -s modern_home_manager/tests
```
