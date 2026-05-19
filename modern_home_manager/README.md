# Modern Home Manager

`modern_home_manager` is now an independent Flask app with its own SQLite database and simulator. It does not depend on the root MySQL/TCP project.

## Structure

- `app.py`: Flask web server and JSON API.
- `database.py`: SQLite schema, seed data, dashboard queries, updates.
- `init_db.py`: Creates `home_manager.db` with seed data.
- `simulator.py`: Writes changing sensor and actuator data into the SQLite DB.
- `templates/dashboard.html`: Dashboard page.
- `static/script.js`: Fetches API data and handles room selection, toggles, and browser location.
- `static/styles.css`: Dashboard styling.

## Run

Install dependencies:

```powershell
python -m pip install -r modern_home_manager/requirements.txt
```

Initialize the database:

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

## Simulator

In another terminal, run one simulated batch:

```powershell
python -m modern_home_manager.simulator --once
```

Or keep writing values every 5 seconds:

```powershell
python -m modern_home_manager.simulator --interval 5
```

The simulator writes directly to:

```text
modern_home_manager/home_manager.db
```

Refresh the dashboard to see updated readings.

## API

- `GET /api/dashboard`: Full dashboard payload.
- `GET /api/rooms/<room_id>`: One room with its sensors and actuators.
- `POST /api/actuators/<actuator_id>/toggle`: Toggle or set an actuator. Body: `{"active": true}`.
- `POST /api/location`: Store browser geolocation. Body: `{"latitude": 37.5, "longitude": 127.0, "accuracy": 20}`.
- `POST /api/reset`: Recreate the SQLite database.

## Tests

```powershell
python -m unittest discover -s modern_home_manager/tests
```
