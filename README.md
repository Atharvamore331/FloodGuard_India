# FloodGuard India

FloodGuard India is a flood risk dashboard with a Flask API and a static web frontend. Clone this repository to any supported computer and run it locally; the project does not depend on the original author's folder path.

## Requirements

- Python 3.10 or newer
- Git
- Internet access for the first dependency installation and live weather data
- MySQL is optional for local use. Without it, database-backed account features will be unavailable.

## Get the project

```sh
git clone https://github.com/Atharvamore331/FloodGuard_India.git
cd FloodGuard_India
```

## Run on Windows

Double-click `run_project.bat`, or from PowerShell run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run_project.ps1
```

The launcher creates `.venv` in the repository, installs required packages, and opens the local frontend. To start only the API, use `start_api.bat` after installing dependencies with `python -m pip install -r requirements.txt`.

## Run on macOS or Linux

```sh
bash start_local.sh
```

The script creates a local virtual environment, installs dependencies, and starts the API and frontend. Open <http://127.0.0.1:5500/index.html> if the browser does not open automatically. Press Ctrl+C to stop the services.

## Run manually on any platform

From the repository root, create and activate a virtual environment, then install dependencies:

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python api.py
```

macOS/Linux:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python api.py
```

In a second terminal, serve the frontend:

```sh
python -m http.server 5500 --directory frontend
```

Then open <http://127.0.0.1:5500/index.html>. The API status endpoint is <http://127.0.0.1:5000/api/status>.

## Optional local services and credentials

For MySQL-backed accounts, create the `floodguard_db` database and set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, and `DB_NAME` in your environment. Email, SMS, and live weather integrations also need credentials. On Windows, copy `local.env.example.ps1` to `local.env.ps1` and enter your own values there; `local.env.ps1` is excluded from Git. Never commit API keys, passwords, or provider tokens.

Some integrations need accounts with their respective providers. The dashboard and risk API can start without notification credentials. Hosted deployment settings are configured separately from local `.env` files.
